use std::path::{Path, PathBuf};
use std::process::Command;

use serde_json::Value;

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("crate lives under repo/crates/mustmatch-cli")
        .to_path_buf()
}

fn run_rust(args: &[&str], expected_exit: i32) -> Value {
    let output = Command::new(env!("CARGO_BIN_EXE_mustmatch-cli"))
        .args(args)
        .current_dir(repo_root())
        .output()
        .expect("run Rust mustmatch-cli");
    assert_eq!(output.status.code(), Some(expected_exit));
    serde_json::from_slice(&output.stdout).expect("Rust command emits JSON")
}

fn run_python(args: &[&str], expected_exit: i32) -> Value {
    let root = repo_root();
    let src = root.join("src");
    let output = Command::new("uv")
        .args([
            "run",
            "python",
            "-c",
            "import sys; from mustmatch.cli import main; raise SystemExit(main(sys.argv[1:]))",
        ])
        .args(args)
        .current_dir(&root)
        .env("PYTHONPATH", src)
        .output()
        .expect("run Python mustmatch CLI");
    assert_eq!(output.status.code(), Some(expected_exit));
    serde_json::from_slice(&output.stdout).expect("Python command emits JSON")
}

fn sorted_lint_rules(value: &Value) -> Vec<String> {
    let mut rules: Vec<String> = value["findings"]
        .as_array()
        .expect("findings array")
        .iter()
        .map(|finding| finding["rule"].as_str().expect("rule string").to_string())
        .collect();
    rules.sort();
    rules
}

#[test]
fn lint_json_matches_python_on_shared_fixtures() {
    for (fixture, expected_exit) in [
        ("tests/fixtures/rust-quality/lint-findings.md", 1),
        ("tests/fixtures/rust-quality/lint-clean-directive.md", 0),
    ] {
        let args = ["lint", fixture, "--json"];
        let rust = run_rust(&args, expected_exit);
        let python = run_python(&args, expected_exit);

        assert_eq!(rust["status"], python["status"]);
        assert_eq!(rust["finding_count"], python["finding_count"]);
        assert_eq!(sorted_lint_rules(&rust), sorted_lint_rules(&python));
    }
}

#[test]
fn verify_matrix_json_matches_python_on_shared_fixture() {
    let args = [
        "verify-matrix",
        "tests/fixtures/rust-quality/verify-matrix-design.md",
        "--repo-root",
        ".",
        "--json",
    ];
    let rust = run_rust(&args, 1);
    let python = run_python(&args, 1);

    assert_eq!(rust["status"], python["status"]);
    assert_eq!(rust["references_checked"], python["references_checked"]);
    assert_eq!(rust["failure_count"], python["failure_count"]);

    let rust_statuses = reference_statuses(&rust);
    let python_statuses = reference_statuses(&python);
    assert_eq!(rust_statuses, python_statuses);
}

fn reference_statuses(value: &Value) -> Vec<(String, String)> {
    let mut statuses: Vec<(String, String)> = value["results"]
        .as_array()
        .expect("results array")
        .iter()
        .map(|item| {
            (
                item["reference"]
                    .as_str()
                    .expect("reference string")
                    .to_string(),
                item["status"].as_str().expect("status string").to_string(),
            )
        })
        .collect();
    statuses.sort();
    statuses
}
