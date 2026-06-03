use std::collections::HashMap;
use std::fs;
use std::path::{Component, Path, PathBuf};

use mustmatch_core::{
    Block, ParseResult, Table, TableRowData, build_table_rows, get_table_for_block, parse_markdown,
};
use tempfile::TempDir;

use crate::context::{ContextRegistry, ContextSettings};
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
    let files = collect_markdown_files(&args.paths);
    if files.is_empty() {
        if !args.quiet {
            eprintln!("No markdown files found");
        }
        return 0;
    }

    let mut summary = Summary::default();
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
        for case in cases {
            match runner.run_block(&case.block, case.row.as_ref()) {
                Ok(BlockOutcome::Passed) => {
                    summary.passed += 1;
                    if args.verbose {
                        println!("PASS {}", case.label);
                    }
                }
                Ok(BlockOutcome::Skipped) => {
                    summary.skipped += 1;
                    if args.verbose {
                        println!("SKIP {}", case.label);
                    }
                }
                Err(message) => {
                    summary.failed += 1;
                    if !args.quiet {
                        eprintln!("FAIL {}: {message}", case.label);
                    }
                    if args.fail_fast {
                        print_summary(&summary, args.quiet);
                        return 1;
                    }
                }
            }
        }
    }
    print_summary(&summary, args.quiet);
    if summary.failed == 0 { 0 } else { 1 }
}

const TEST_HELP: &str = "mustmatch-cli test - Run code blocks in markdown files as tests.\n\nUsage:\n    mustmatch-cli test [OPTIONS] [PATHS...]\n\nOptions:\n    -v, --verbose        Show each block result\n    -q, --quiet          Suppress summary and failure diagnostics\n    -x, --fail-fast      Stop after the first failure\n    --timeout SECONDS    Per-block timeout (default: 30)\n    --lang LANG          Language filter: all or bash\n    -h, --help           Show this help";

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
            || block.language == "python"
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
        if block.language == "python" {
            return Ok(BlockOutcome::Skipped);
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
        self.path
            .parent()
            .unwrap_or_else(|| Path::new("."))
            .to_path_buf()
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
        let context_name = block.directives.get("context").map(String::as_str);
        let settings = self.contexts.resolve_scoped(
            context_name,
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

    use super::MarkdownRunner;

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
}
