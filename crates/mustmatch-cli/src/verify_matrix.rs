use std::ffi::OsString;
use std::fs;
use std::path::{Component, Path, PathBuf};
use std::sync::LazyLock;

use regex::Regex;
use serde_json::{Value, json};

static TABLE_ROW_RE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^\|(.+)\|\s*$").expect("valid regex"));
static CODE_RE: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"`([^`]+)`").expect("valid regex"));

const EXPECTED_MISSING_MARKER: &str = "expected-missing";

const REPO_ROOT_FILE_NAMES: &[&str] = &[
    "CLAUDE.md",
    "Cargo.lock",
    "Cargo.toml",
    "Makefile",
    "README.md",
    "pyproject.toml",
    "rustfmt.toml",
    "uv.lock",
];
const REPO_FILE_EXTENSIONS: &[&str] = &[
    ".json", ".lock", ".md", ".py", ".rs", ".sh", ".toml", ".txt", ".yaml", ".yml", ".zig",
];
const REPO_PATH_PREFIXES: &[&str] = &[
    ".march/", "bench/", "crates/", "docs/", "lib/", "scripts/", "spec/", "src/", "test/", "tests/",
];

pub(crate) const HELP: &str = "mustmatch verify-matrix - Verify proof-matrix file references resolve inside a repo.\n\nUsage:\n    mustmatch verify-matrix [OPTIONS] DESIGN --repo-root ROOT\n\nArguments:\n    DESIGN               Markdown design file to inspect\n\nOptions:\n    --repo-root ROOT     Repo root used to resolve backticked file references\n    --json               Emit structured JSON instead of human-readable lines\n    -h, --help           Show this help";

#[derive(Debug, Clone)]
pub(crate) struct VerifyMatrixArgs {
    design: PathBuf,
    repo_root: PathBuf,
    json: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct TableRef {
    line: usize,
    reference: String,
}

pub(crate) fn parse_args(args: &[String]) -> Result<VerifyMatrixArgs, i32> {
    let mut design: Option<PathBuf> = None;
    let mut repo_root: Option<PathBuf> = None;
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
            "--repo-root" => {
                index += 1;
                if index >= args.len() {
                    eprintln!("Error: --repo-root requires a value");
                    return Err(2);
                }
                repo_root = Some(PathBuf::from(&args[index]));
            }
            _ if arg.starts_with('-') => {
                eprintln!("Error: unknown option: {arg}");
                return Err(2);
            }
            _ => {
                if design.is_some() {
                    eprintln!("Error: too many arguments");
                    return Err(2);
                }
                design = Some(PathBuf::from(arg));
            }
        }
        index += 1;
    }

    let Some(design) = design else {
        eprintln!("Error: design path required");
        return Err(2);
    };
    let Some(repo_root) = repo_root else {
        eprintln!("Error: --repo-root is required");
        return Err(2);
    };

    Ok(VerifyMatrixArgs {
        design,
        repo_root,
        json,
    })
}

pub(crate) fn run(args: VerifyMatrixArgs) -> i32 {
    if !args.design.is_file() {
        eprintln!("Error: design file not found: {}", args.design.display());
        return 2;
    }
    if !args.repo_root.is_dir() {
        eprintln!("Error: repo root not found: {}", args.repo_root.display());
        return 2;
    }

    let design = fs::canonicalize(&args.design).unwrap_or_else(|_| args.design.clone());
    let repo_root = fs::canonicalize(&args.repo_root).unwrap_or_else(|_| args.repo_root.clone());
    let result = match verify_matrix(&design, &repo_root) {
        Ok(result) => result,
        Err(message) => {
            eprintln!("Error: {message}");
            return 2;
        }
    };

    if args.json {
        match serde_json::to_string_pretty(&result) {
            Ok(output) => println!("{output}"),
            Err(err) => {
                eprintln!("Error: failed to serialize verify-matrix result: {err}");
                return 1;
            }
        }
    } else if let Some(results) = result["results"].as_array() {
        for item in results {
            println!(
                "{} line {}: {} -> {}",
                item["status"].as_str().unwrap_or("").to_ascii_uppercase(),
                item["line"].as_u64().unwrap_or(0),
                item["reference"].as_str().unwrap_or(""),
                item["resolved_path"].as_str().unwrap_or("")
            );
        }
    }

    if result["failure_count"].as_u64().unwrap_or(0) == 0 {
        0
    } else {
        1
    }
}

fn verify_matrix(design: &Path, repo_root: &Path) -> Result<Value, String> {
    let text = fs::read_to_string(design)
        .map_err(|err| format!("failed to read design file {}: {err}", design.display()))?;
    let refs = collect_table_refs(&text);
    let mut results: Vec<Value> = Vec::new();
    let mut failure_count = 0usize;

    for table_ref in refs {
        let reference_path = Path::new(&table_ref.reference);
        let (resolved_path, status) = if reference_path.is_absolute() {
            (resolve_path(reference_path), "invalid")
        } else {
            let resolved_path = resolve_path(&repo_root.join(reference_path));
            let status = if !resolved_path.starts_with(repo_root) {
                "invalid"
            } else if resolved_path.exists() {
                "ok"
            } else {
                "missing"
            };
            (resolved_path, status)
        };

        if status != "ok" {
            failure_count += 1;
        }

        results.push(json!({
            "line": table_ref.line,
            "reference": table_ref.reference,
            "resolved_path": resolved_path.to_string_lossy(),
            "status": status,
        }));
    }

    Ok(json!({
        "design": design.to_string_lossy(),
        "repo_root": repo_root.to_string_lossy(),
        "references_checked": results.len(),
        "failure_count": failure_count,
        "status": if failure_count == 0 { "pass" } else { "fail" },
        "results": results,
    }))
}

fn collect_table_refs(text: &str) -> Vec<TableRef> {
    let mut refs = Vec::new();
    for (index, line) in text.lines().enumerate() {
        let Some(row) = TABLE_ROW_RE.captures(line) else {
            continue;
        };
        let Some(row_body) = row.get(1) else {
            continue;
        };
        for cell in row_body.as_str().split('|') {
            for captures in CODE_RE.captures_iter(cell) {
                let Some(span) = captures.get(0) else {
                    continue;
                };
                if has_expected_missing_marker(&cell[..span.start()]) {
                    continue;
                }
                let Some(code) = captures.get(1) else {
                    continue;
                };
                if looks_like_repo_path(code.as_str()) {
                    refs.push(TableRef {
                        line: index + 1,
                        reference: code.as_str().to_string(),
                    });
                }
            }
        }
    }
    refs
}

fn has_expected_missing_marker(prefix: &str) -> bool {
    let prefix = prefix.trim_end();
    let Some(before_marker) = prefix.strip_suffix(EXPECTED_MISSING_MARKER) else {
        return false;
    };
    before_marker.is_empty()
        || before_marker
            .chars()
            .last()
            .is_some_and(char::is_whitespace)
}

fn looks_like_repo_path(value: &str) -> bool {
    let value = value.trim();
    if value.is_empty() {
        return false;
    }
    if value.chars().any(char::is_whitespace) {
        return false;
    }
    if ["://", "${", "&&", "||", ";", "|", ">", "<"]
        .iter()
        .any(|token| value.contains(token))
    {
        return false;
    }
    if value.starts_with('~') || value.starts_with('$') {
        return false;
    }

    let candidate = Path::new(value);
    if REPO_ROOT_FILE_NAMES.contains(&value) {
        return true;
    }
    if candidate.is_absolute() {
        return path_has_repo_extension(candidate) || path_file_name_is_repo_root_name(candidate);
    }
    if REPO_PATH_PREFIXES
        .iter()
        .any(|prefix| value.starts_with(prefix))
    {
        return true;
    }
    path_has_repo_extension(candidate)
}

fn path_has_repo_extension(path: &Path) -> bool {
    path.extension()
        .and_then(|extension| extension.to_str())
        .map(|extension| REPO_FILE_EXTENSIONS.contains(&format!(".{extension}").as_str()))
        .unwrap_or(false)
}

fn path_file_name_is_repo_root_name(path: &Path) -> bool {
    path.file_name()
        .and_then(|name| name.to_str())
        .map(|name| REPO_ROOT_FILE_NAMES.contains(&name))
        .unwrap_or(false)
}

fn resolve_path(path: &Path) -> PathBuf {
    if let Ok(resolved) = fs::canonicalize(path) {
        return resolved;
    }

    let mut suffix: Vec<OsString> = Vec::new();
    let mut current = path;
    while let Some(parent) = current.parent() {
        if let Some(name) = current.file_name() {
            suffix.push(name.to_os_string());
        }
        if let Ok(mut resolved) = fs::canonicalize(parent) {
            for part in suffix.iter().rev() {
                resolved.push(part);
            }
            return lexical_normalize(&resolved);
        }
        current = parent;
    }

    lexical_normalize(path)
}

fn lexical_normalize(path: &Path) -> PathBuf {
    let mut normalized = PathBuf::new();
    for component in path.components() {
        match component {
            Component::Prefix(prefix) => normalized.push(prefix.as_os_str()),
            Component::RootDir => normalized.push(component.as_os_str()),
            Component::CurDir => {}
            Component::ParentDir => {
                if !normalized.pop() {
                    normalized.push("..");
                }
            }
            Component::Normal(part) => normalized.push(part),
        }
    }
    normalized
}

#[cfg(test)]
mod tests {
    use super::{collect_table_refs, lexical_normalize, looks_like_repo_path, verify_matrix};
    use std::path::Path;
    use tempfile::tempdir;

    #[test]
    fn repo_path_heuristic_rejects_false_positive_traps() {
        for value in [
            "",
            "   ",
            "https://service.example/v1/resource",
            "printf ok && rm -rf output",
            "echo $REPORT_PATH",
            "$REPORT_PATH",
            "${REPORT_PATH}",
            "~/README.md",
            "docs/read me.md",
            "cat docs/file.md | mustmatch ok",
        ] {
            assert!(!looks_like_repo_path(value), "{value}");
        }
    }

    #[test]
    fn repo_path_heuristic_accepts_python_parity_paths() {
        for value in [
            "README.md",
            "docs/guide.md",
            "crates/mustmatch-cli/src/main.rs",
            "relative.toml",
            "/tmp/design.md",
        ] {
            assert!(looks_like_repo_path(value), "{value}");
        }
    }

    #[test]
    fn table_refs_only_collect_backticked_repo_paths_from_table_rows() {
        let text = "not a table `README.md`\n| ok | `README.md` |\n| route | `https://example.test/a` |\n| missing | `docs/nope.md` |\n";
        let refs = collect_table_refs(text);

        assert_eq!(refs.len(), 2);
        assert_eq!(refs[0].line, 2);
        assert_eq!(refs[0].reference, "README.md");
        assert_eq!(refs[1].reference, "docs/nope.md");
    }

    #[test]
    fn table_refs_skip_only_immediately_marked_expected_missing_path() {
        let text = "| behavior | location | assertion |\n| --- | --- | --- |\n| present | `README.md` | expected-missing `docs/none.md` |\n| mixed | `docs/nope.md` | expected-missing `docs/escaped.md` then `docs/real.md` |\n| accidental | | notexpected-missing `docs/accidental.md` |\n";
        let refs = collect_table_refs(text);

        assert_eq!(refs.len(), 4);
        assert_eq!(refs[0].reference, "README.md");
        assert_eq!(refs[1].reference, "docs/nope.md");
        assert_eq!(refs[2].reference, "docs/real.md");
        assert_eq!(refs[3].reference, "docs/accidental.md");
    }

    #[test]
    fn verify_matrix_still_reports_unescaped_missing_reference() {
        let dir = tempdir().expect("tempdir");
        let repo_root = dir.path().join("repo");
        std::fs::create_dir_all(&repo_root).expect("repo root");
        let design = dir.path().join("design.md");
        std::fs::write(
            &design,
            "| behavior | location |\n| --- | --- |\n| missing | `docs/nope.md` |\n",
        )
        .expect("design");

        let result = verify_matrix(&design, &repo_root).expect("verify result");

        assert_eq!(result["references_checked"], 1);
        assert_eq!(result["failure_count"], 1);
        assert_eq!(result["results"][0]["reference"], "docs/nope.md");
        assert_eq!(result["results"][0]["status"], "missing");
    }

    #[test]
    fn lexical_normalize_removes_parent_segments_without_requiring_existence() {
        assert_eq!(
            lexical_normalize(Path::new("/repo/docs/../README.md")),
            Path::new("/repo/README.md")
        );
    }

    #[cfg(unix)]
    #[test]
    fn verify_matrix_rejects_symlink_escape() {
        let dir = tempdir().expect("tempdir");
        let repo_root = dir.path().join("repo");
        let outside = dir.path().join("outside");
        std::fs::create_dir_all(repo_root.join("docs")).expect("repo docs");
        std::fs::create_dir_all(&outside).expect("outside dir");
        std::fs::write(repo_root.join("README.md"), "# repo\n").expect("readme");
        std::os::unix::fs::symlink(&outside, repo_root.join("docs/outside")).expect("symlink");
        let design = dir.path().join("design.md");
        std::fs::write(
            &design,
            "| behavior | location |\n| --- | --- |\n| escape | `docs/outside/missing.md` |\n",
        )
        .expect("design");

        let result = verify_matrix(&design, &repo_root).expect("verify result");

        assert_eq!(result["failure_count"], 1);
        assert_eq!(result["results"][0]["status"], "invalid");
    }
}
