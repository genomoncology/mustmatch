use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::LazyLock;

use regex::Regex;
use serde_json::{Value, json};

static MUSTMATCH_JSON_RE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\|\s*mustmatch\s+json\b").expect("valid regex"));
static SHORT_LIKE_RE: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r#"\|\s*mustmatch\s+like\s+("([^"]*)"|'([^']*)')"#).expect("valid regex")
});
static FENCE_RE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^```(?P<info>.*)$").expect("valid regex"));

pub(crate) const HELP: &str = "mustmatch-cli lint - Lint markdown spec assertions without executing them.\n\nUsage:\n    mustmatch-cli lint [OPTIONS] SPEC\n\nArguments:\n    SPEC                 Markdown spec file to inspect\n\nOptions:\n    --min-like-len N     Flag mustmatch like literals shorter than this length (default: 10)\n    --json               Emit structured JSON instead of human-readable lines\n    -h, --help           Show this help";

#[derive(Debug, Clone)]
pub(crate) struct LintArgs {
    spec: PathBuf,
    min_like_len: usize,
    json: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct ShellBlock {
    start_line: usize,
    language: String,
    block: String,
}

pub(crate) fn parse_args(args: &[String]) -> Result<LintArgs, i32> {
    let mut spec: Option<PathBuf> = None;
    let mut min_like_len = 10usize;
    let mut json = false;

    let mut index = 0;
    while index < args.len() {
        let arg = &args[index];
        match arg.as_str() {
            "-h" | "--help" => {
                println!("{HELP}");
                return Err(0);
            }
            "--json" => json = true,
            "--min-like-len" => {
                index += 1;
                if index >= args.len() {
                    eprintln!("Error: --min-like-len requires a value");
                    return Err(2);
                }
                match args[index].parse::<usize>() {
                    Ok(value) => min_like_len = value,
                    Err(_) => {
                        eprintln!("Error: --min-like-len must be an integer");
                        return Err(2);
                    }
                }
            }
            _ if arg.starts_with('-') => {
                eprintln!("Error: unknown option: {arg}");
                return Err(2);
            }
            _ => {
                if spec.is_some() {
                    eprintln!("Error: too many arguments");
                    return Err(2);
                }
                spec = Some(PathBuf::from(arg));
            }
        }
        index += 1;
    }

    let Some(spec) = spec else {
        eprintln!("Error: spec path required");
        return Err(2);
    };

    Ok(LintArgs {
        spec,
        min_like_len,
        json,
    })
}

pub(crate) fn run(args: LintArgs) -> i32 {
    if !args.spec.is_file() {
        eprintln!("Error: spec file not found: {}", args.spec.display());
        return 2;
    }

    let spec = fs::canonicalize(&args.spec).unwrap_or_else(|_| args.spec.clone());
    let result = match lint_spec_file(&spec, args.min_like_len) {
        Ok(result) => result,
        Err(message) => {
            eprintln!("Error: {message}");
            return 1;
        }
    };

    if args.json {
        match serde_json::to_string_pretty(&result) {
            Ok(output) => println!("{output}"),
            Err(err) => {
                eprintln!("Error: failed to serialize lint result: {err}");
                return 1;
            }
        }
    } else {
        println!("spec={}", result["spec"].as_str().unwrap_or(""));
        println!("findings={}", result["finding_count"].as_u64().unwrap_or(0));
        if let Some(findings) = result["findings"].as_array() {
            for finding in findings {
                println!(
                    "FAIL line {} {}: {}",
                    finding["line"].as_u64().unwrap_or(0),
                    finding["rule"].as_str().unwrap_or(""),
                    finding["message"].as_str().unwrap_or("")
                );
            }
        }
    }

    if result["finding_count"].as_u64().unwrap_or(0) == 0 {
        0
    } else {
        1
    }
}

fn lint_spec_file(spec: &Path, min_like_len: usize) -> Result<Value, String> {
    let text = fs::read_to_string(spec)
        .map_err(|err| format!("failed to read spec file {}: {err}", spec.display()))?;
    let mut findings: Vec<Value> = Vec::new();

    for (index, line) in text.lines().enumerate() {
        let line_number = index + 1;
        if MUSTMATCH_JSON_RE.is_match(line) {
            findings.push(json!({
                "line": line_number,
                "rule": "invalid-mustmatch-mode",
                "message": "uses unsupported `mustmatch json` syntax",
                "text": line.trim(),
            }));
        }

        if let Some(captures) = SHORT_LIKE_RE.captures(line) {
            let literal = captures
                .get(2)
                .or_else(|| captures.get(3))
                .map(|item| item.as_str())
                .unwrap_or("");
            if literal.len() < min_like_len {
                findings.push(json!({
                    "line": line_number,
                    "rule": "short-like-pattern",
                    "message": format!(
                        "uses short `mustmatch like` literal \"{}\" ({} chars)",
                        literal,
                        literal.len()
                    ),
                    "text": line.trim(),
                }));
            }
        }
    }

    for shell_block in collect_shell_blocks(&text) {
        if !matches!(
            shell_block.language.as_str(),
            "bash" | "sh" | "shell" | "zsh"
        ) {
            continue;
        }

        let result = run_bash_syntax_check(&shell_block.block)?;
        if let Some(message) = result {
            findings.push(json!({
                "line": shell_block.start_line,
                "rule": "invalid-shell-syntax",
                "message": message,
                "text": shell_block.block.lines().next().unwrap_or(""),
            }));
        }
    }

    Ok(json!({
        "spec": spec.to_string_lossy(),
        "finding_count": findings.len(),
        "status": if findings.is_empty() { "pass" } else { "fail" },
        "findings": findings,
    }))
}

fn collect_shell_blocks(text: &str) -> Vec<ShellBlock> {
    let mut blocks = Vec::new();
    let mut current_language: Option<String> = None;
    let mut current_start = 0usize;
    let mut current_lines: Vec<&str> = Vec::new();

    for (index, line) in text.lines().enumerate() {
        let line_number = index + 1;
        if current_language.is_none() {
            if let Some(captures) = FENCE_RE.captures(line) {
                let info = captures
                    .name("info")
                    .map(|item| item.as_str().trim())
                    .unwrap_or("");
                let language = info
                    .split_once(char::is_whitespace)
                    .map(|(first, _)| first)
                    .unwrap_or(info)
                    .to_lowercase();
                current_language = Some(language);
                current_start = line_number + 1;
                current_lines.clear();
            }
            continue;
        }

        if line.trim() == "```" {
            blocks.push(ShellBlock {
                start_line: current_start,
                language: current_language.take().unwrap_or_default(),
                block: current_lines.join("\n"),
            });
            current_start = 0;
            current_lines.clear();
            continue;
        }

        current_lines.push(line);
    }

    blocks
}

fn run_bash_syntax_check(block: &str) -> Result<Option<String>, String> {
    let mut child = Command::new("bash")
        .arg("-n")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|err| {
            if err.kind() == std::io::ErrorKind::NotFound {
                "bash is required to lint shell code blocks".to_string()
            } else {
                format!("failed to run bash -n: {err}")
            }
        })?;

    if let Some(mut stdin) = child.stdin.take() {
        stdin
            .write_all(block.as_bytes())
            .map_err(|err| format!("failed to write shell block to bash -n: {err}"))?;
    }

    let output = child
        .wait_with_output()
        .map_err(|err| format!("failed to wait for bash -n: {err}"))?;
    if output.status.success() {
        return Ok(None);
    }

    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
    if stderr.is_empty() {
        Ok(Some("bash -n failed".to_string()))
    } else {
        Ok(Some(stderr))
    }
}

#[cfg(test)]
mod tests {
    use super::{collect_shell_blocks, lint_spec_file};
    use tempfile::tempdir;

    #[test]
    fn directive_bearing_shell_fence_uses_first_info_token() {
        let blocks = collect_shell_blocks("```bash timeout=5\necho ok\n```\n");

        assert_eq!(blocks.len(), 1);
        assert_eq!(blocks[0].language, "bash");
        assert_eq!(blocks[0].start_line, 2);
        assert_eq!(blocks[0].block, "echo ok");
    }

    #[test]
    fn lint_reports_three_python_parity_rule_families() {
        let dir = tempdir().expect("tempdir");
        let spec = dir.path().join("lint.md");
        std::fs::write(
            &spec,
            "```bash timeout=5\necho '{\"status\":\"ok\"}' | mustmatch json\necho alpha | mustmatch like \"beta\"\nif then\nfi\n```\n",
        )
        .expect("write fixture");

        let result = lint_spec_file(&spec, 10).expect("lint result");
        let rules: Vec<&str> = result["findings"]
            .as_array()
            .expect("findings array")
            .iter()
            .filter_map(|finding| finding["rule"].as_str())
            .collect();

        assert_eq!(result["finding_count"], 3);
        assert!(rules.contains(&"invalid-mustmatch-mode"));
        assert!(rules.contains(&"short-like-pattern"));
        assert!(rules.contains(&"invalid-shell-syntax"));
    }
}
