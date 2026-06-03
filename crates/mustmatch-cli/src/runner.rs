use std::fs;
use std::path::{Path, PathBuf};

use mustmatch_core::{Block, parse_markdown};

use crate::context::ContextRegistry;
use crate::expect::{assert_output_matches, mode as expect_mode};
use crate::named_runs::{
    NamedRuns, block_id, expect_target, expected_exit, is_output_block, is_run_block,
    result_stream, selected_stream, timeout_for,
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
        for case in runner.cases() {
            match runner.run_block(&case.block) {
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
}

enum BlockOutcome {
    Passed,
    Skipped,
}

struct MarkdownRunner {
    path: PathBuf,
    lang: String,
    timeout: u64,
    blocks: Vec<Block>,
    contexts: ContextRegistry,
    named_runs: NamedRuns,
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
            blocks: parsed.blocks,
            contexts,
            named_runs,
        })
    }

    fn cases(&self) -> Vec<Case> {
        self.blocks
            .iter()
            .filter(|block| self.include_block(block))
            .map(|block| {
                let heading = block.name.as_deref().unwrap_or("unnamed");
                Case {
                    block: block.clone(),
                    label: format!("{heading} (line {}) [{}]", block.line_start, block.language),
                }
            })
            .collect()
    }

    fn include_block(&self, block: &Block) -> bool {
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

    fn run_block(&mut self, block: &Block) -> Result<BlockOutcome, String> {
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
            let default_cwd = self.default_cwd();
            self.named_runs
                .run(&ident, &mut self.contexts, &default_cwd, self.timeout)?;
            return Ok(BlockOutcome::Passed);
        }
        if is_output_block(block) {
            self.run_output(block)?;
            return Ok(BlockOutcome::Passed);
        }
        if block.language == "bash" {
            if !bash_block_has_mustmatch_pipe(&block.content) {
                return Ok(BlockOutcome::Skipped);
            }
            self.run_bash_block(block)?;
            return Ok(BlockOutcome::Passed);
        }
        if block.language == "python" {
            return Ok(BlockOutcome::Skipped);
        }
        Ok(BlockOutcome::Skipped)
    }

    fn run_console(&mut self, block: &Block) -> Result<(), String> {
        let context_name = block.directives.get("context").map(String::as_str);
        let settings = self.contexts.resolve(context_name, &self.default_cwd())?;
        let expected_code = expected_exit(block)?;
        let stream = selected_stream(block)?;
        for (command, expected) in parse_console_examples(&block.content)? {
            let default_cwd = self.default_cwd();
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

    fn run_output(&mut self, block: &Block) -> Result<(), String> {
        let target = expect_target(block)
            .ok_or_else(|| "output blocks require expect=<run-id>".to_string())?;
        if !self.named_runs.has(target) {
            return Err(format!("unknown run id {target:?}"));
        }
        let default_cwd = self.default_cwd();
        let result = self
            .named_runs
            .run(target, &mut self.contexts, &default_cwd, self.timeout)?;
        let stream = if block.directives.contains_key("stream") {
            selected_stream(block)?
        } else {
            let run_block = self
                .named_runs
                .block(target)
                .ok_or_else(|| format!("unknown run id {target:?}"))?;
            selected_stream(run_block)?
        };
        assert_output_matches(
            result_stream(&result, stream),
            block.content.trim_matches('\n'),
            &block.language,
            expect_mode(&block.directives),
        )
    }

    fn run_bash_block(&mut self, block: &Block) -> Result<(), String> {
        let context_name = block.directives.get("context").map(String::as_str);
        let settings = self.contexts.resolve(context_name, &self.default_cwd())?;
        let default_cwd = self.default_cwd();
        let content = self.named_runs.substitute(
            &block.content,
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

    fn default_cwd(&self) -> PathBuf {
        self.path
            .parent()
            .unwrap_or_else(|| Path::new("."))
            .to_path_buf()
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
