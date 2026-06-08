use std::collections::HashMap;
use std::fs;
use std::path::{Component, Path, PathBuf};

use mustmatch_core::{
    Block, ParseResult, Table, TableRowData, build_table_rows, get_table_for_block, parse_markdown,
};
use tempfile::TempDir;

use crate::context::{ConfigKey, ContextRegistry, ContextSettings};
use crate::expect::{assert_output_matches, mode as expect_mode};
use crate::named_runs::{
    NamedRuns, block_id, expect_target, expected_exit, is_output_block, is_run_block,
    normalize_lookup, render_value, result_stream, selected_stream, timeout_for,
};
use crate::process::run_bash;

#[derive(Debug, Clone)]
pub(crate) struct TestArgs {
    pub(crate) paths: Vec<PathBuf>,
    pub(crate) verbose: bool,
    pub(crate) quiet: bool,
    pub(crate) fail_fast: bool,
    pub(crate) timeout: u64,
    pub(crate) lang: String,
}

#[derive(Default)]
struct Summary {
    passed: usize,
    failed: usize,
    skipped: usize,
    xfailed: usize,
    xpassed: usize,
}

/// An `xfail` directive: the block is expected to fail. `reason` is the optional
/// `xfail="..."` text; `strict` (a sibling `strict` directive) turns an
/// unexpected pass (XPASS) into a real failure.
struct Xfail {
    reason: Option<String>,
    strict: bool,
}

fn parse_xfail(block: &Block) -> Option<Xfail> {
    if !block.directives.contains_key("xfail") {
        return None;
    }
    let reason = block
        .directives
        .get("xfail")
        .map(String::as_str)
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .map(str::to_string);
    Some(Xfail {
        reason,
        strict: block.directives.contains_key("strict"),
    })
}

fn reason_suffix(spec: &Xfail) -> String {
    match &spec.reason {
        Some(reason) => format!(" ({reason})"),
        None => String::new(),
    }
}

struct SuiteLifecycle {
    key: ConfigKey,
    contexts: ContextRegistry,
}

pub(crate) fn parse_test_args(args: &[String]) -> Result<TestArgs, i32> {
    let mut paths = Vec::new();
    let mut verbose = false;
    let mut quiet = false;
    let mut fail_fast = false;
    let mut timeout = 30;
    let mut lang = "all".to_string();
    let mut index = 0;
    while index < args.len() {
        match args[index].as_str() {
            "-h" | "--help" => {
                println!("{TEST_HELP}");
                return Err(0);
            }
            "-v" | "--verbose" => verbose = true,
            "-q" | "--quiet" => quiet = true,
            "-x" | "--fail-fast" => fail_fast = true,
            "--timeout" => {
                index += 1;
                let Some(value) = args.get(index) else {
                    eprintln!("Error: --timeout requires a value");
                    return Err(2);
                };
                timeout = match value.parse::<u64>() {
                    Ok(value) => value,
                    Err(_) => {
                        eprintln!("Error: --timeout must be an integer");
                        return Err(2);
                    }
                };
            }
            "--lang" => {
                index += 1;
                let Some(value) = args.get(index) else {
                    eprintln!("Error: --lang requires a value");
                    return Err(2);
                };
                if value != "all" && value != "bash" {
                    eprintln!("Error: --lang must be all or bash");
                    return Err(2);
                }
                lang = value.clone();
            }
            value if value.starts_with('-') => {
                eprintln!("Error: unknown option: {value}");
                return Err(2);
            }
            value => paths.push(PathBuf::from(value)),
        }
        index += 1;
    }
    if paths.is_empty() {
        paths.push(PathBuf::from("."));
    }
    Ok(TestArgs {
        paths,
        verbose,
        quiet,
        fail_fast,
        timeout,
        lang,
    })
}

pub(crate) fn run(args: TestArgs) -> i32 {
    let missing_paths = missing_explicit_paths(&args.paths);
    if !missing_paths.is_empty() {
        if !args.quiet {
            for path in missing_paths {
                eprintln!("Path not found: {}", path.display());
            }
        }
        return 1;
    }

    let files = collect_markdown_files(&args.paths);
    if files.is_empty() {
        if !args.quiet {
            eprintln!("No markdown files found");
        }
        return 0;
    }

    let mut summary = Summary::default();
    let mut suites: Vec<SuiteLifecycle> = Vec::new();
    let mut stop = false;
    for file in files {
        let mut runner = match MarkdownRunner::new(&file, &args.lang, args.timeout) {
            Ok(runner) => runner,
            Err(message) => {
                summary.failed += 1;
                if !args.quiet {
                    eprintln!("FAIL {}: {message}", file.display());
                }
                if args.fail_fast {
                    break;
                }
                continue;
            }
        };
        if let Err(message) = ensure_suite_started(&mut suites, &file, &runner.contexts) {
            summary.failed += 1;
            if !args.quiet {
                eprintln!("FAIL {}: {message}", file.display());
            }
            break;
        }
        let cases = match runner.cases() {
            Ok(cases) => cases,
            Err(message) => {
                summary.failed += 1;
                if !args.quiet {
                    eprintln!("FAIL {}: {message}", file.display());
                }
                if args.fail_fast {
                    break;
                }
                continue;
            }
        };
        runner.register_context_uses(&cases);
        if let Err(message) = runner.run_file_setup() {
            summary.failed += 1;
            if !args.quiet {
                eprintln!("FAIL {}: {message}", file.display());
            }
            break;
        }
        let mut file_failed = false;
        for case in cases {
            let outcome = runner.run_block(&case.block, case.row.as_ref());
            let teardown = runner.finish_case();
            let xfail = parse_xfail(&case.block);
            match (outcome, teardown) {
                (Ok(BlockOutcome::Passed), Ok(())) => match &xfail {
                    Some(spec) if spec.strict => {
                        summary.failed += 1;
                        file_failed = true;
                        if !args.quiet {
                            eprintln!(
                                "FAIL {}: XPASS — block marked xfail strict passed unexpectedly{}",
                                case.label,
                                reason_suffix(spec)
                            );
                        }
                        if args.fail_fast {
                            stop = true;
                            break;
                        }
                    }
                    Some(spec) => {
                        summary.xpassed += 1;
                        if args.verbose {
                            println!("XPASS {}{}", case.label, reason_suffix(spec));
                        }
                    }
                    None => {
                        summary.passed += 1;
                        if args.verbose {
                            println!("PASS {}", case.label);
                        }
                    }
                },
                (Ok(BlockOutcome::Skipped), Ok(())) => {
                    summary.skipped += 1;
                    if args.verbose {
                        println!("SKIP {}", case.label);
                    }
                }
                (Ok(_), Err(message)) => {
                    summary.failed += 1;
                    file_failed = true;
                    if !args.quiet {
                        eprintln!("FAIL {}: {message}", case.label);
                    }
                    if args.fail_fast {
                        stop = true;
                        break;
                    }
                }
                (Err(message), teardown_result) => match &xfail {
                    Some(spec) => {
                        summary.xfailed += 1;
                        if args.verbose {
                            println!("XFAIL {}{}", case.label, reason_suffix(spec));
                        }
                        if let Err(teardown_message) = teardown_result {
                            summary.failed += 1;
                            file_failed = true;
                            if !args.quiet {
                                eprintln!("FAIL {} teardown: {teardown_message}", case.label);
                            }
                            if args.fail_fast {
                                stop = true;
                                break;
                            }
                        }
                    }
                    None => {
                        summary.failed += 1;
                        file_failed = true;
                        if !args.quiet {
                            eprintln!("FAIL {}: {message}", case.label);
                            if let Err(teardown_message) = teardown_result {
                                eprintln!("FAIL {} teardown: {teardown_message}", case.label);
                            }
                        }
                        if args.fail_fast {
                            stop = true;
                            break;
                        }
                    }
                },
            }
        }
        if let Err(message) = runner.finish_contexts() {
            if !args.quiet {
                eprintln!("FAIL {} context teardown: {message}", file.display());
            }
            if !file_failed {
                summary.failed += 1;
                file_failed = true;
                if args.fail_fast {
                    stop = true;
                }
            }
        }
        if let Err(message) = runner.run_file_teardown() {
            if !args.quiet {
                eprintln!("FAIL {} teardown: {message}", file.display());
            }
            if !file_failed {
                summary.failed += 1;
                if args.fail_fast {
                    stop = true;
                }
            }
        }
        if stop {
            break;
        }
    }
    let had_failure = summary.failed > 0;
    for suite in suites.iter_mut().rev() {
        if let Err(message) = suite.contexts.run_suite_teardown() {
            if !args.quiet {
                eprintln!("FAIL suite teardown: {message}");
            }
            if !had_failure {
                summary.failed += 1;
            }
        }
    }
    print_summary(&summary, args.quiet);
    if summary.failed == 0 { 0 } else { 1 }
}

fn ensure_suite_started(
    suites: &mut Vec<SuiteLifecycle>,
    file: &Path,
    contexts: &ContextRegistry,
) -> Result<(), String> {
    let key = contexts.config_key();
    if suites.iter().any(|suite| suite.key == key) {
        return Ok(());
    }
    let mut suite_contexts = ContextRegistry::new(file)?;
    suite_contexts.run_suite_setup()?;
    suites.push(SuiteLifecycle {
        key,
        contexts: suite_contexts,
    });
    Ok(())
}

const TEST_HELP: &str = "mustmatch test - Run code blocks in markdown files as tests.\n\nUsage:\n    mustmatch test [OPTIONS] [PATHS...]\n\nOptions:\n    -v, --verbose        Show each block result\n    -q, --quiet          Suppress summary and failure diagnostics\n    -x, --fail-fast      Stop after the first failure\n    --timeout SECONDS    Per-block timeout (default: 30)\n    --lang LANG          Language filter: all or bash\n    -h, --help           Show this help";

#[derive(Clone)]
struct Case {
    block: Block,
    label: String,
    row: Option<RowContext>,
}

#[derive(Clone)]
struct RowContext {
    key: String,
    table_key: String,
    row: TableRowData,
}

enum BlockOutcome {
    Passed,
    Skipped,
}

struct MarkdownRunner {
    path: PathBuf,
    lang: String,
    timeout: u64,
    parsed: ParseResult,
    contexts: ContextRegistry,
    named_runs: NamedRuns,
    section_roots: HashMap<String, TempDir>,
    transient_roots: Vec<TempDir>,
}

impl MarkdownRunner {
    fn new(path: &Path, lang: &str, timeout: u64) -> Result<Self, String> {
        let content = fs::read_to_string(path)
            .map_err(|err| format!("failed to read {}: {err}", path.display()))?;
        let parsed = parse_markdown(&content);
        let contexts = ContextRegistry::new(path)?;
        let named_runs = NamedRuns::new(&parsed.blocks);
        Ok(Self {
            path: path.to_path_buf(),
            lang: lang.to_string(),
            timeout,
            parsed,
            contexts,
            named_runs,
            section_roots: HashMap::new(),
            transient_roots: Vec::new(),
        })
    }

    fn cases(&self) -> Result<Vec<Case>, String> {
        for block in self
            .parsed
            .blocks
            .iter()
            .filter(|block| is_file_block(block))
        {
            validate_file_block(block)?;
        }

        let mut cases = Vec::new();
        for block in self
            .parsed
            .blocks
            .iter()
            .filter(|block| self.include_block(block))
        {
            let heading = block.name.as_deref().unwrap_or("unnamed");
            let base_label = format!("{heading} (line {}) [{}]", block.line_start, block.language);
            if is_row_block(block) {
                let (table_key, rows) = self.rows_for(block)?;
                for (index, row) in rows.into_iter().enumerate() {
                    let row_label = row_label(&row).unwrap_or_else(|| format!("row-{}", index + 1));
                    let key = format!("{table_key}:{}", index + 1);
                    cases.push(Case {
                        block: block.clone(),
                        label: format!("{base_label} [{row_label}]"),
                        row: Some(RowContext {
                            key,
                            table_key: table_key.clone(),
                            row,
                        }),
                    });
                }
            } else {
                cases.push(Case {
                    block: block.clone(),
                    label: base_label,
                    row: None,
                });
            }
        }
        Ok(cases)
    }

    fn include_block(&self, block: &Block) -> bool {
        if is_file_block(block) {
            return false;
        }
        if self.lang != "all"
            && block.language != self.lang
            && !(self.lang == "bash" && (is_output_block(block) || is_console_block(block)))
        {
            return false;
        }
        is_console_block(block)
            || is_run_block(block)
            || is_output_block(block)
            || block.language == "bash"
    }

    fn register_context_uses(&mut self, cases: &[Case]) {
        for case in cases {
            if let Some(context) = context_name(&case.block) {
                self.contexts
                    .register_context_use(context, case.row.as_ref().map(|row| row.key.as_str()));
            }
        }
    }

    fn run_file_setup(&mut self) -> Result<(), String> {
        self.contexts.run_file_setup(&self.default_cwd())
    }

    fn run_file_teardown(&mut self) -> Result<(), String> {
        self.contexts.run_file_teardown()
    }

    fn finish_case(&mut self) -> Result<(), String> {
        self.contexts.finish_case()
    }

    fn finish_contexts(&mut self) -> Result<(), String> {
        self.contexts.finish_all_contexts()
    }

    fn run_block(
        &mut self,
        block: &Block,
        row: Option<&RowContext>,
    ) -> Result<BlockOutcome, String> {
        if block.directives.contains_key("skip") {
            return Ok(BlockOutcome::Skipped);
        }
        if is_console_block(block) {
            self.run_console(block)?;
            return Ok(BlockOutcome::Passed);
        }
        if is_run_block(block) {
            let ident =
                block_id(block).ok_or_else(|| "run blocks require id=<name>".to_string())?;
            let default_cwd = self.default_cwd_for(block, row)?;
            self.prepare_block_cwd(block, row, &default_cwd)?;
            self.named_runs.run_with_row(
                &ident,
                row.map(|row| (row.key.as_str(), &row.row)),
                &mut self.contexts,
                &default_cwd,
                self.timeout,
            )?;
            return Ok(BlockOutcome::Passed);
        }
        if is_output_block(block) {
            self.run_output(block, row)?;
            return Ok(BlockOutcome::Passed);
        }
        if block.language == "bash" {
            if !bash_block_has_mustmatch_pipe(&block.content) {
                return Ok(BlockOutcome::Skipped);
            }
            self.run_bash_block(block, row)?;
            return Ok(BlockOutcome::Passed);
        }
        Ok(BlockOutcome::Skipped)
    }

    fn run_console(&mut self, block: &Block) -> Result<(), String> {
        let default_cwd = self.default_cwd_for(block, None)?;
        let settings = self.prepare_block_cwd(block, None, &default_cwd)?;
        let expected_code = expected_exit(block)?;
        let stream = selected_stream(block)?;
        for (command, expected) in parse_console_examples(&block.content)? {
            let command = self.named_runs.substitute(
                &command,
                &mut self.contexts,
                &default_cwd,
                self.timeout,
            )?;
            let timeout = timeout_for(block, self.timeout);
            let result = run_bash(&command, &settings.cwd, &settings.env, timeout)
                .map_err(|err| format!("console command failed to start: {err}"))?;
            if result.timed_out {
                return Err(format!("console command timed out after {timeout} seconds"));
            }
            if result.exit_code != expected_code {
                return Err(format!(
                    "console command expected exit {expected_code}, actual exit {}, selected stream {stream}: {command}",
                    result.exit_code
                ));
            }
            if !expected.is_empty() {
                assert_output_matches(
                    result_stream(&result, stream),
                    &expected,
                    "markdown",
                    expect_mode(&block.directives),
                )?;
            }
        }
        Ok(())
    }

    fn run_output(&mut self, block: &Block, row: Option<&RowContext>) -> Result<(), String> {
        let target = expect_target(block)
            .ok_or_else(|| "output blocks require expect=<run-id>".to_string())?;
        if !self.named_runs.has(target) {
            return Err(format!("unknown run id {target:?}"));
        }
        if let Some(row) = row {
            let run_block = self
                .named_runs
                .block(target)
                .cloned()
                .ok_or_else(|| format!("unknown run id {target:?}"))?;
            if !is_row_block(&run_block) {
                return Err(format!(
                    "expect={target} each_row requires matching run each_row"
                ));
            }
            let (run_table_key, _) = self.rows_for(&run_block)?;
            if run_table_key != row.table_key {
                return Err(format!(
                    "expect={target} table does not match run table: expected {}, got {}",
                    run_table_key, row.table_key
                ));
            }
        }
        let default_cwd = self.default_cwd_for(block, row)?;
        if let Some(run_block) = self.named_runs.block(target).cloned() {
            self.prepare_block_cwd(&run_block, row, &default_cwd)?;
        }
        let result = self.named_runs.run_with_row(
            target,
            row.map(|row| (row.key.as_str(), &row.row)),
            &mut self.contexts,
            &default_cwd,
            self.timeout,
        )?;
        let stream = if block.directives.contains_key("stream") {
            selected_stream(block)?.to_string()
        } else {
            let run_block = self
                .named_runs
                .block(target)
                .ok_or_else(|| format!("unknown run id {target:?}"))?;
            selected_stream(run_block)?.to_string()
        };
        let expected = self.named_runs.substitute_with_row(
            block.content.trim_matches('\n'),
            row.map(|row| &row.row),
            &mut self.contexts,
            &default_cwd,
            self.timeout,
        )?;
        assert_output_matches(
            result_stream(&result, &stream),
            &expected,
            &block.language,
            expect_mode(&block.directives),
        )
    }

    fn run_bash_block(&mut self, block: &Block, row: Option<&RowContext>) -> Result<(), String> {
        let default_cwd = self.default_cwd_for(block, row)?;
        let settings = self.prepare_block_cwd(block, row, &default_cwd)?;
        let content = self.named_runs.substitute_with_row(
            &block.content,
            row.map(|row| &row.row),
            &mut self.contexts,
            &default_cwd,
            self.timeout,
        )?;
        let timeout = timeout_for(block, self.timeout);
        let result = run_bash(&content, &settings.cwd, &settings.env, timeout)
            .map_err(|err| format!("bash block failed to start: {err}"))?;
        if result.timed_out {
            return Err(format!("bash block timed out after {timeout} seconds"));
        }
        if result.exit_code == 0 {
            Ok(())
        } else {
            Err(format!(
                "bash block exited {}\n{}{}",
                result.exit_code, result.stdout, result.stderr
            ))
        }
    }

    fn rows_for(&self, block: &Block) -> Result<(String, Vec<TableRowData>), String> {
        let table = self.table_for(block)?;
        let table_key = table_key(&table);
        let (_, rows) = build_table_rows(&table.headers, &table.rows);
        if rows.is_empty() {
            Err(format!("each_row table {table_key:?} has no rows"))
        } else {
            Ok((table_key, rows))
        }
    }

    fn table_for(&self, block: &Block) -> Result<Table, String> {
        let each_row = non_empty_directive(block, "each_row");
        let table = non_empty_directive(block, "table");
        match (each_row, table) {
            (Some(left), Some(right)) => {
                if normalize_lookup(left) != normalize_lookup(right) {
                    return Err(format!(
                        "each_row table {left:?} conflicts with table={right:?}"
                    ));
                }
                self.named_table(left)
            }
            (Some(name), None) | (None, Some(name)) => self.named_table(name),
            (None, None) => get_table_for_block(&self.parsed, block)
                .ok_or_else(|| "each_row directive requires a preceding table".to_string()),
        }
    }

    fn named_table(&self, name: &str) -> Result<Table, String> {
        let normalized = normalize_lookup(name);
        self.parsed
            .tables
            .iter()
            .find(|table| normalize_lookup(&table_name(table)) == normalized)
            .cloned()
            .ok_or_else(|| format!("unknown table {name:?}"))
    }

    fn default_cwd(&self) -> PathBuf {
        doc_dir(&self.path)
    }

    fn section_root_for(&mut self, block: &Block) -> Result<PathBuf, String> {
        let key = section_key(block);
        if !self.section_roots.contains_key(&key) {
            let tmp = TempDir::new().map_err(|err| format!("failed to create tempdir: {err}"))?;
            self.section_roots.insert(key.clone(), tmp);
        }
        self.section_roots
            .get(&key)
            .map(|tmp| tmp.path().to_path_buf())
            .ok_or_else(|| "failed to create section tempdir".to_string())
    }

    fn section_has_file_blocks(&self, block: &Block) -> bool {
        let key = section_key(block);
        self.parsed
            .blocks
            .iter()
            .any(|candidate| is_file_block(candidate) && section_key(candidate) == key)
    }

    fn default_cwd_for(
        &mut self,
        block: &Block,
        row: Option<&RowContext>,
    ) -> Result<PathBuf, String> {
        if !self.section_has_file_blocks(block) {
            if row.is_some() {
                let tmp =
                    TempDir::new().map_err(|err| format!("failed to create row tempdir: {err}"))?;
                let path = tmp.path().to_path_buf();
                self.transient_roots.push(tmp);
                return Ok(path);
            }
            return Ok(self.default_cwd());
        }

        let section_root = self.section_root_for(block)?;
        let Some(row) = row else {
            return Ok(section_root);
        };
        let row_root = section_root
            .join(".mustmatch-rows")
            .join(normalize_lookup(&row.key));
        fs::create_dir_all(&row_root).map_err(|err| {
            format!(
                "failed to create row fixture dir {}: {err}",
                row_root.display()
            )
        })?;
        Ok(row_root)
    }

    fn prepare_block_cwd(
        &mut self,
        block: &Block,
        row: Option<&RowContext>,
        default_cwd: &Path,
    ) -> Result<ContextSettings, String> {
        let settings = self.contexts.resolve_scoped(
            context_name(block),
            default_cwd,
            row.map(|row| row.key.as_str()),
        )?;
        self.materialize_applicable_files(block, row, &settings.cwd)?;
        Ok(settings)
    }

    fn materialize_applicable_files(
        &mut self,
        consumer: &Block,
        row: Option<&RowContext>,
        cwd: &Path,
    ) -> Result<(), String> {
        let consumer_section = section_key(consumer);
        let files: Vec<Block> = self
            .parsed
            .blocks
            .iter()
            .filter(|block| {
                is_file_block(block)
                    && block.line_start < consumer.line_start
                    && section_key(block) == consumer_section
            })
            .cloned()
            .collect();

        for file_block in files {
            if is_row_block(&file_block) {
                let Some(row) = row else {
                    continue;
                };
                let (table_key, _) = self.rows_for(&file_block)?;
                if table_key != row.table_key {
                    continue;
                }
                self.materialize_file(&file_block, Some(row), cwd)?;
            } else {
                self.materialize_file(&file_block, row, cwd)?;
            }
        }
        Ok(())
    }

    fn materialize_file(
        &mut self,
        block: &Block,
        row: Option<&RowContext>,
        cwd: &Path,
    ) -> Result<(), String> {
        let relative = fixture_relative_path(block)?;
        let target = cwd.join(&relative);
        if let Some(parent) = target.parent() {
            fs::create_dir_all(parent).map_err(|err| {
                format!("failed to create fixture dir {}: {err}", parent.display())
            })?;
        }
        let content = self.named_runs.substitute_with_row(
            &block.content,
            row.map(|row| &row.row),
            &mut self.contexts,
            cwd,
            self.timeout,
        )?;
        fs::write(&target, content)
            .map_err(|err| format!("failed to write fixture file {}: {err}", target.display()))
    }
}

fn missing_explicit_paths(paths: &[PathBuf]) -> Vec<&Path> {
    paths
        .iter()
        .map(PathBuf::as_path)
        .filter(|path| !path.exists())
        .collect()
}

fn collect_markdown_files(paths: &[PathBuf]) -> Vec<PathBuf> {
    let mut files = Vec::new();
    for path in paths {
        collect_one(path, &mut files);
    }
    files.sort();
    files.dedup();
    files
}

fn collect_one(path: &Path, files: &mut Vec<PathBuf>) {
    if path.is_file() {
        if path.extension().and_then(|value| value.to_str()) == Some("md") {
            files.push(path.to_path_buf());
        }
        return;
    }
    if !path.is_dir() {
        return;
    }
    let Ok(entries) = fs::read_dir(path) else {
        return;
    };
    for entry in entries.flatten() {
        collect_one(&entry.path(), files);
    }
}

fn is_console_block(block: &Block) -> bool {
    block.language == "console" && block.directives.contains_key("mustmatch")
}

fn is_row_block(block: &Block) -> bool {
    block.directives.contains_key("each_row")
}

fn is_file_block(block: &Block) -> bool {
    block.directives.contains_key("file")
}

fn validate_file_block(block: &Block) -> Result<(), String> {
    fixture_relative_path(block)?;
    for directive in [
        "run",
        "mustmatch-run",
        "expect",
        "for",
        "output",
        "mustmatch-output",
    ] {
        if block.directives.contains_key(directive) {
            return Err(format!(
                "file blocks cannot also use {directive}= (line {})",
                block.line_start
            ));
        }
    }
    Ok(())
}

fn fixture_relative_path(block: &Block) -> Result<PathBuf, String> {
    let value = non_empty_directive(block, "file").ok_or_else(|| {
        format!(
            "file directive requires a relative path (line {})",
            block.line_start
        )
    })?;
    if value.starts_with('\\') || value.as_bytes().get(1).copied() == Some(b':') {
        return Err(format!(
            "file path {value:?} must be relative and stay under the fixture cwd"
        ));
    }
    let path = PathBuf::from(value);
    if path.is_absolute() {
        return Err(format!(
            "file path {value:?} must be relative and stay under the fixture cwd"
        ));
    }
    for component in path.components() {
        match component {
            Component::Normal(_) | Component::CurDir => {}
            Component::ParentDir | Component::RootDir | Component::Prefix(_) => {
                return Err(format!(
                    "file path {value:?} must be relative and stay under the fixture cwd"
                ));
            }
        }
    }
    Ok(path)
}

/// Directory a markdown document's blocks run from. A bare filename
/// (`demo.md`) has an empty-string parent, not `None`, so treat any empty
/// parent as `.` — otherwise blocks spawn with an empty cwd and fail to start.
fn doc_dir(path: &Path) -> PathBuf {
    match path.parent() {
        Some(parent) if !parent.as_os_str().is_empty() => parent.to_path_buf(),
        _ => PathBuf::from("."),
    }
}

fn section_key(block: &Block) -> String {
    match block.context_lines.as_slice() {
        [_, h2, ..] => format!("section:{h2}"),
        [] => "section:document".to_string(),
        lines => format!("section:{}", lines[lines.len() - 1]),
    }
}

fn non_empty_directive<'a>(block: &'a Block, key: &str) -> Option<&'a str> {
    block
        .directives
        .get(key)
        .map(String::as_str)
        .map(str::trim)
        .filter(|value| !value.is_empty())
}

fn context_name(block: &Block) -> Option<&str> {
    non_empty_directive(block, "context")
}

fn table_name(table: &Table) -> String {
    table
        .context
        .last()
        .cloned()
        .unwrap_or_else(|| "unnamed".to_string())
}

fn table_key(table: &Table) -> String {
    format!(
        "{}:line{}",
        normalize_lookup(&table_name(table)),
        table.line_start
    )
}

fn row_label(row: &TableRowData) -> Option<String> {
    row.get("label").map(|value| render_value(&value))
}

fn bash_block_has_mustmatch_pipe(script: &str) -> bool {
    script.lines().any(|line| {
        let code = code_before_shell_comment(line);
        code.contains("| mustmatch") || code.contains("|mustmatch")
    })
}

fn code_before_shell_comment(line: &str) -> &str {
    let mut single_quoted = false;
    let mut double_quoted = false;
    let mut escaped = false;

    for (index, ch) in line.char_indices() {
        if escaped {
            escaped = false;
            continue;
        }
        if double_quoted && ch == '\\' {
            escaped = true;
            continue;
        }
        match ch {
            '\'' if !double_quoted => single_quoted = !single_quoted,
            '"' if !single_quoted => double_quoted = !double_quoted,
            '#' if !single_quoted
                && !double_quoted
                && (index == 0 || line[..index].ends_with(char::is_whitespace)) =>
            {
                return &line[..index];
            }
            _ => {}
        }
    }
    line
}

fn parse_console_examples(content: &str) -> Result<Vec<(String, String)>, String> {
    let mut examples = Vec::new();
    let mut command: Option<String> = None;
    let mut expected_lines: Vec<String> = Vec::new();
    for line in content.lines() {
        if let Some(rest) = line.strip_prefix("$ ") {
            flush_console(&mut examples, &mut command, &mut expected_lines);
            command = Some(rest.to_string());
        } else if command.is_some() {
            expected_lines.push(line.to_string());
        } else if !line.trim().is_empty() {
            return Err("console mustmatch blocks must start commands with `$ `".to_string());
        }
    }
    flush_console(&mut examples, &mut command, &mut expected_lines);
    if examples.is_empty() {
        Err("console mustmatch blocks require at least one `$ command` line".to_string())
    } else {
        Ok(examples)
    }
}

fn flush_console(
    examples: &mut Vec<(String, String)>,
    command: &mut Option<String>,
    expected_lines: &mut Vec<String>,
) {
    if let Some(command) = command.take() {
        examples.push((
            command,
            expected_lines.join("\n").trim_matches('\n').to_string(),
        ));
    }
    expected_lines.clear();
}

fn print_summary(summary: &Summary, quiet: bool) {
    if quiet {
        return;
    }
    let mut parts = Vec::new();
    if summary.passed > 0 {
        parts.push(format!("{} passed", summary.passed));
    }
    if summary.failed > 0 {
        parts.push(format!("{} failed", summary.failed));
    }
    if summary.skipped > 0 {
        parts.push(format!("{} skipped", summary.skipped));
    }
    if summary.xfailed > 0 {
        parts.push(format!("{} xfailed", summary.xfailed));
    }
    if summary.xpassed > 0 {
        parts.push(format!("{} xpassed", summary.xpassed));
    }
    println!(
        "{}",
        if parts.is_empty() {
            "no tests".to_string()
        } else {
            parts.join(", ")
        }
    );
}

#[cfg(test)]
mod tests {
    use std::fs;
    use std::path::Path;

    use tempfile::tempdir;

    use super::{MarkdownRunner, TestArgs, doc_dir, run};

    #[test]
    fn doc_dir_treats_bare_filename_as_dot() {
        use std::path::PathBuf;
        // A bare filename's parent is Some("") — must resolve to "." so blocks
        // spawn with a valid cwd (`mustmatch test README.md`).
        assert_eq!(doc_dir(Path::new("README.md")), PathBuf::from("."));
        assert_eq!(doc_dir(Path::new("spec/doc.md")), PathBuf::from("spec"));
        assert_eq!(doc_dir(Path::new("/abs/doc.md")), PathBuf::from("/abs"));
    }

    fn run_quiet(path: std::path::PathBuf) -> i32 {
        run(TestArgs {
            paths: vec![path],
            verbose: false,
            quiet: true,
            fail_fast: false,
            timeout: 5,
            lang: "all".to_string(),
        })
    }

    #[test]
    fn xfail_block_that_fails_keeps_suite_green() {
        let dir = tempdir().expect("tempdir");
        let path = write_markdown(
            dir.path(),
            "# Doc\n\n## Known gap\n\n```bash xfail\nmustmatch() { return 1; }\nprintf x | mustmatch like x\n```\n",
        );
        assert_eq!(run_quiet(path), 0);
    }

    #[test]
    fn xfail_block_that_passes_is_xpass_and_stays_green() {
        let dir = tempdir().expect("tempdir");
        let path = write_markdown(
            dir.path(),
            "# Doc\n\n## Fixed\n\n```bash xfail\nmustmatch() { return 0; }\nprintf x | mustmatch like x\n```\n",
        );
        assert_eq!(run_quiet(path), 0);
    }

    #[test]
    fn strict_xfail_block_that_passes_fails_the_suite() {
        let dir = tempdir().expect("tempdir");
        let path = write_markdown(
            dir.path(),
            "# Doc\n\n## Strict\n\n```bash xfail strict\nmustmatch() { return 0; }\nprintf x | mustmatch like x\n```\n",
        );
        assert_eq!(run_quiet(path), 1);
    }

    fn write_markdown(dir: &Path, content: &str) -> std::path::PathBuf {
        let path = dir.join("doc.md");
        fs::write(&path, content).expect("write markdown fixture");
        path
    }

    fn unwrap_err(result: Result<impl Sized, String>) -> String {
        match result {
            Ok(_) => panic!("expected error"),
            Err(err) => err,
        }
    }

    #[test]
    fn sections_without_file_blocks_keep_document_cwd() {
        let dir = tempdir().expect("tempdir");
        fs::write(dir.path().join("sidecar.txt"), "sidecar-ready\n").expect("write sidecar");
        let path = write_markdown(
            dir.path(),
            r#"# Doc

## Reads local sidecar

```bash
mustmatch() { grep -q sidecar-ready; }
cat sidecar.txt | mustmatch like 'sidecar-ready'
```
"#,
        );
        let mut runner = MarkdownRunner::new(&path, "all", 5).expect("runner");
        let cases = runner.cases().expect("cases");

        assert_eq!(cases.len(), 1);
        runner
            .run_block(&cases[0].block, None)
            .expect("plain sections should run from the markdown directory");
    }

    #[test]
    fn file_blocks_reject_unsafe_paths_and_conflicts() {
        let dir = tempdir().expect("tempdir");
        for (name, fence, expected) in [
            (
                "empty.md",
                "```json file=\n{}\n```\n",
                "file directive requires a relative path",
            ),
            (
                "parent.md",
                "```json file=../escape.json\n{}\n```\n",
                "must be relative and stay under the fixture cwd",
            ),
            (
                "absolute.md",
                "```json file=/tmp/escape.json\n{}\n```\n",
                "must be relative and stay under the fixture cwd",
            ),
            (
                "conflict.md",
                "```json file=config.json expect=run-output\n{}\n```\n",
                "file blocks cannot also use expect=",
            ),
        ] {
            let path = dir.path().join(name);
            fs::write(&path, format!("# Doc\n\n{fence}")).expect("write markdown fixture");
            let runner = MarkdownRunner::new(&path, "all", 5).expect("runner");
            let err = unwrap_err(runner.cases());
            assert!(err.contains(expected), "{err}");
        }
    }

    #[test]
    fn row_template_errors_name_missing_columns() {
        let dir = tempdir().expect("tempdir");
        let path = write_markdown(
            dir.path(),
            r#"# Doc

## Rows

| input | str:label |
|-------|-----------|
| 2     | bad-row   |

```bash run id=missing each_row="Rows"
printf '{{missing}}\n'
```
"#,
        );
        let mut runner = MarkdownRunner::new(&path, "all", 5).expect("runner");
        let cases = runner.cases().expect("cases");

        assert!(cases[0].label.contains("[bad-row]"));
        let err = unwrap_err(runner.run_block(&cases[0].block, cases[0].row.as_ref()));
        assert!(err.contains("unknown row column \"missing\""));
    }

    #[test]
    fn each_row_reports_unknown_or_conflicting_tables_before_execution() {
        let dir = tempdir().expect("tempdir");
        let missing_path = write_markdown(
            dir.path(),
            r#"# Doc

```bash run id=missing-table each_row="Missing Rows"
echo never
```
"#,
        );
        let missing_runner = MarkdownRunner::new(&missing_path, "all", 5).expect("runner");
        let err = unwrap_err(missing_runner.cases());
        assert!(err.contains("unknown table \"Missing Rows\""));

        let conflict_path = write_markdown(
            dir.path(),
            r#"# Doc

## Rows

| input |
|-------|
| 1     |

```bash run id=conflict each_row="Rows" table="Other Rows"
echo never
```
"#,
        );
        let conflict_runner = MarkdownRunner::new(&conflict_path, "all", 5).expect("runner");
        let err = unwrap_err(conflict_runner.cases());
        assert!(err.contains("each_row table \"Rows\" conflicts with table=\"Other Rows\""));
    }

    #[test]
    fn scenario_outline_rejects_mismatched_run_and_expect_tables() {
        let dir = tempdir().expect("tempdir");
        let path = write_markdown(
            dir.path(),
            r#"# Doc

## Input Rows

| value |
|-------|
| one   |

```bash run id=item each_row="Input Rows"
printf '{{value}}\n'
```

## Output Rows

| value |
|-------|
| two   |

```text expect=item each_row="Output Rows" contains
{{value}}
```
"#,
        );
        let mut runner = MarkdownRunner::new(&path, "all", 5).expect("runner");
        let cases = runner.cases().expect("cases");

        runner
            .run_block(&cases[0].block, cases[0].row.as_ref())
            .expect("run row should pass");
        let err = unwrap_err(runner.run_block(&cases[1].block, cases[1].row.as_ref()));
        assert!(err.contains("expect=item table does not match run table"));
    }

    #[test]
    fn row_contexts_use_fresh_context_cwds() {
        let dir = tempdir().expect("tempdir");
        fs::write(
            dir.path().join("mustmatch.toml"),
            r#"[contexts.rowtmp]
cwd = "{tmp}"
"#,
        )
        .expect("write config");
        let path = write_markdown(
            dir.path(),
            r#"# Doc

## Rows

| str:label |
|-----------|
| first     |
| second    |

```bash run id=leak-check each_row="Rows" context=rowtmp
if [ -e leak ]; then
  exit 7
fi
touch leak
```
"#,
        );
        let mut runner = MarkdownRunner::new(&path, "all", 5).expect("runner");
        let cases = runner.cases().expect("cases");

        assert_eq!(cases.len(), 2);
        for case in &cases {
            runner
                .run_block(&case.block, case.row.as_ref())
                .expect("row cwd should be isolated");
        }
    }

    #[test]
    fn suite_and_file_teardown_run_on_fail_fast_failure() {
        let dir = tempdir().expect("tempdir");
        fs::write(
            dir.path().join("mustmatch.toml"),
            r#"[suite]
setup = ["printf suite > {root}/suite-body.txt"]
teardown = ["rm -f {root}/suite-body.txt"]

[file]
setup = ["printf file > {root}/file-body.txt"]
teardown = ["rm -f {root}/file-body.txt"]
"#,
        )
        .expect("write config");
        let path = write_markdown(
            dir.path(),
            r#"# Doc

## Fails

```bash
mustmatch() { grep -q expected; }
printf wrong | mustmatch "expected"
```
"#,
        );

        let code = run(TestArgs {
            paths: vec![path],
            verbose: false,
            quiet: true,
            fail_fast: true,
            timeout: 5,
            lang: "all".to_string(),
        });

        assert_eq!(code, 1);
        assert!(!dir.path().join("suite-body.txt").exists());
        assert!(!dir.path().join("file-body.txt").exists());
    }

    #[test]
    fn row_context_teardown_runs_for_each_row_scope() {
        let dir = tempdir().expect("tempdir");
        fs::write(
            dir.path().join("mustmatch.toml"),
            r#"[contexts.rowtmp]
cwd = "{tmp}"
setup = ["printf S >> {root}/lifecycle.log"]
teardown = ["printf T >> {root}/lifecycle.log"]
"#,
        )
        .expect("write config");
        let path = write_markdown(
            dir.path(),
            r#"# Doc

## Rows

| str:label |
|-----------|
| first     |
| second    |

```bash each_row="Rows" context=rowtmp
mustmatch() { grep -q ok; }
printf ok | mustmatch like ok
```
"#,
        );

        let code = run(TestArgs {
            paths: vec![path],
            verbose: false,
            quiet: true,
            fail_fast: false,
            timeout: 5,
            lang: "all".to_string(),
        });

        assert_eq!(code, 0);
        assert_eq!(
            fs::read_to_string(dir.path().join("lifecycle.log")).expect("read log"),
            "STST"
        );
    }

    #[test]
    fn context_teardown_runs_when_fail_fast_stops_before_later_use() {
        let dir = tempdir().expect("tempdir");
        fs::write(
            dir.path().join("mustmatch.toml"),
            r#"[contexts.cleanup]
            cwd = "."
            setup = ["printf state > {root}/state.txt"]
            teardown = ["rm -f {root}/state.txt"]
            "#,
        )
        .expect("write config");
        let path = write_markdown(
            dir.path(),
            r#"# Doc

## Fails

```bash context=cleanup
cat state.txt >/dev/null
mustmatch() { grep -q expected; }
printf wrong | mustmatch "expected"
```

## Would Reuse Context

```bash context=cleanup
cat state.txt | mustmatch like state
```
"#,
        );

        let code = run(TestArgs {
            paths: vec![path],
            verbose: false,
            quiet: true,
            fail_fast: true,
            timeout: 5,
            lang: "all".to_string(),
        });

        assert_eq!(code, 1);
        assert!(!dir.path().join("state.txt").exists());
    }

    #[test]
    fn suite_setup_failure_stops_later_files() {
        let dir = tempdir().expect("tempdir");
        let first = dir.path().join("first");
        let second = dir.path().join("second");
        fs::create_dir_all(&first).expect("first dir");
        fs::create_dir_all(&second).expect("second dir");
        fs::write(
            first.join("mustmatch.toml"),
            r#"[suite]
            setup = ["printf state > {root}/state.txt; exit 9"]
            teardown = ["rm -f {root}/state.txt"]
            "#,
        )
        .expect("write failing config");
        fs::write(second.join("mustmatch.toml"), "").expect("write second config");
        let first_doc = write_markdown(&first, "# First\n");
        let second_doc = write_markdown(
            &second,
            r#"# Second

## Should Not Run

```bash
printf ran > ran.txt
cat ran.txt | mustmatch like ran
```
"#,
        );

        let code = run(TestArgs {
            paths: vec![first_doc, second_doc],
            verbose: false,
            quiet: true,
            fail_fast: false,
            timeout: 5,
            lang: "all".to_string(),
        });

        assert_eq!(code, 1);
        assert!(!first.join("state.txt").exists());
        assert!(!second.join("ran.txt").exists());
    }

    #[test]
    fn file_setup_failure_runs_file_teardown() {
        let dir = tempdir().expect("tempdir");
        fs::write(
            dir.path().join("mustmatch.toml"),
            r#"[file]
setup = ["printf state > {root}/state.txt; exit 9"]
teardown = ["rm -f {root}/state.txt"]
"#,
        )
        .expect("write config");
        let path = write_markdown(
            dir.path(),
            r#"# Doc

## Should Not Run

```bash
printf ok | mustmatch like ok
```
"#,
        );

        let code = run(TestArgs {
            paths: vec![path],
            verbose: false,
            quiet: true,
            fail_fast: false,
            timeout: 5,
            lang: "all".to_string(),
        });

        assert_eq!(code, 1);
        assert!(!dir.path().join("state.txt").exists());
    }

    #[test]
    fn context_setup_failure_runs_context_teardown() {
        let dir = tempdir().expect("tempdir");
        fs::write(
            dir.path().join("mustmatch.toml"),
            r#"[contexts.cleanup]
cwd = "."
setup = ["printf state > {root}/state.txt; exit 9"]
teardown = ["rm -f {root}/state.txt"]
"#,
        )
        .expect("write config");
        let path = write_markdown(
            dir.path(),
            r#"# Doc

## Context Fails During Setup

```bash context=cleanup
printf ok | mustmatch like ok
```
"#,
        );

        let code = run(TestArgs {
            paths: vec![path],
            verbose: false,
            quiet: true,
            fail_fast: false,
            timeout: 5,
            lang: "all".to_string(),
        });

        assert_eq!(code, 1);
        assert!(!dir.path().join("state.txt").exists());
    }

    #[test]
    fn named_run_context_teardown_runs_after_cached_run_use() {
        let dir = tempdir().expect("tempdir");
        fs::write(
            dir.path().join("mustmatch.toml"),
            r#"[contexts.cleanup]
cwd = "."
setup = ["printf state > {root}/state.txt"]
teardown = ["rm -f {root}/state.txt {root}/body.txt"]
"#,
        )
        .expect("write config");
        let path = write_markdown(
            dir.path(),
            r#"# Doc

## Context Run

```bash run id=context-json context=cleanup
cat state.txt >/dev/null
printf body > body.txt
printf '{"status":"ok"}\n'
```

```json expect=context-json contains
{"status":"ok"}
```

## Cleanup Visible

```bash
mustmatch() { ! grep -q body.txt; }
ls body.txt 2>/dev/null | mustmatch not like body.txt
```
"#,
        );

        let code = run(TestArgs {
            paths: vec![path],
            verbose: false,
            quiet: true,
            fail_fast: false,
            timeout: 5,
            lang: "all".to_string(),
        });

        assert_eq!(code, 0);
        assert!(!dir.path().join("body.txt").exists());
    }
}
