use std::ffi::OsString;
use std::fs;
use std::path::PathBuf;
use std::process::{Command, Output};

use tempfile::tempdir;

fn mustmatch_bin() -> PathBuf {
    PathBuf::from(env!("CARGO_BIN_EXE_mustmatch"))
}

fn run_mustmatch(args: &[&str]) -> Output {
    Command::new(mustmatch_bin())
        .args(args)
        .output()
        .expect("run mustmatch")
}

fn run_mustmatch_in(dir: &std::path::Path, args: &[&str]) -> Output {
    Command::new(mustmatch_bin())
        .current_dir(dir)
        .env("PATH", path_with_mustmatch_bin())
        .args(args)
        .output()
        .expect("run mustmatch")
}

fn path_with_mustmatch_bin() -> OsString {
    let mut paths = vec![
        mustmatch_bin()
            .parent()
            .expect("binary has parent")
            .to_path_buf(),
    ];
    if let Some(existing) = std::env::var_os("PATH") {
        paths.extend(std::env::split_paths(&existing));
    }
    std::env::join_paths(paths).expect("join PATH")
}

fn stdout(output: &Output) -> String {
    String::from_utf8_lossy(&output.stdout).into_owned()
}

fn stderr(output: &Output) -> String {
    String::from_utf8_lossy(&output.stderr).into_owned()
}

#[test]
fn missing_explicit_path_fails_but_empty_directory_is_noop() {
    let dir = tempdir().expect("tempdir");
    let missing = dir.path().join("does-not-exist.md");

    let missing_output = run_mustmatch(&["test", missing.to_str().expect("utf8 path")]);

    assert!(
        !missing_output.status.success(),
        "missing explicit path must fail, stdout={:?}, stderr={:?}",
        stdout(&missing_output),
        stderr(&missing_output)
    );
    let missing_stderr = stderr(&missing_output);
    let missing_stderr_lower = missing_stderr.to_lowercase();
    assert!(
        missing_stderr.contains("does-not-exist.md")
            && (missing_stderr_lower.contains("not found")
                || missing_stderr_lower.contains("does not exist")
                || missing_stderr_lower.contains("missing")),
        "missing path diagnostic should name the path, got: {missing_stderr:?}"
    );

    let empty_dir = tempdir().expect("empty tempdir");
    let empty_output = run_mustmatch(&["test", empty_dir.path().to_str().expect("utf8 path")]);

    assert!(
        empty_output.status.success(),
        "existing empty directory remains a no-op, stdout={:?}, stderr={:?}",
        stdout(&empty_output),
        stderr(&empty_output)
    );
    assert!(stderr(&empty_output).contains("No markdown files found"));
}

#[test]
fn bare_filename_context_root_resolves_to_current_directory() {
    let dir = tempdir().expect("tempdir");
    fs::write(
        dir.path().join("mustmatch.toml"),
        r#"[contexts.demo]
cwd = "{root}"
setup = ["printf root-ok > {root}/root-sentinel.txt"]
"#,
    )
    .expect("write config");
    fs::write(
        dir.path().join("doc.md"),
        r#"# Bare Root

## Context root

```bash context=demo
cat root-sentinel.txt | mustmatch like root-ok
```
"#,
    )
    .expect("write markdown");

    let output = run_mustmatch_in(dir.path(), &["test", "doc.md"]);

    assert!(
        output.status.success(),
        "bare filename context should resolve {{root}} to the current config directory, stdout={:?}, stderr={:?}",
        stdout(&output),
        stderr(&output)
    );
    assert!(dir.path().join("root-sentinel.txt").exists());
}

#[test]
fn invalid_lang_exits_before_green_no_tests_summary() {
    let output = run_mustmatch(&["test", "--lang", "nope"]);

    assert!(!output.status.success(), "invalid --lang must fail");
    let err = stderr(&output);
    assert!(err.contains("--lang must be all or bash"), "stderr={err:?}");
    let combined = format!("{}{}", stdout(&output), err);
    assert!(
        !combined.contains("no tests") && !combined.contains("No markdown files found"),
        "invalid --lang must not be reported as a green no-tests run: {combined:?}"
    );
}

#[test]
fn cyclic_uses_dependency_fails_with_clear_message() {
    let dir = tempdir().expect("tempdir");
    fs::write(
        dir.path().join("cycle.md"),
        r#"# Cycle

## A

```bash run id=a uses=b
printf '{"a":true}\n'
```

```bash run id=b uses=a
printf '{"b":true}\n'
```

```json expect=a contains
{"a":true}
```
"#,
    )
    .expect("write markdown");

    let output = run_mustmatch_in(dir.path(), &["test", "cycle.md"]);

    assert!(!output.status.success(), "cycle must fail");
    assert!(
        stderr(&output).contains("cyclic run dependency"),
        "cycle diagnostic should be clear, stderr={:?}",
        stderr(&output)
    );
}

#[test]
fn setup_failure_diagnostic_redacts_expanded_secret() {
    let dir = tempdir().expect("tempdir");
    let secret = "SYNTHETIC_SUPER_SECRET_VALUE";
    fs::write(
        dir.path().join("mustmatch.toml"),
        format!(
            r#"[contexts.leaky]
cwd = "."
setup = ["printf '${{DEMO_SECRET}}\n' >/dev/null; exit 7"]

[contexts.leaky.env]
DEMO_SECRET = "{secret}"
"#
        ),
    )
    .expect("write config");
    fs::write(
        dir.path().join("doc.md"),
        r#"# Secret

## Context

```bash context=leaky
printf ok | mustmatch like ok
```
"#,
    )
    .expect("write markdown");

    let output = run_mustmatch_in(dir.path(), &["test", "doc.md"]);

    assert!(!output.status.success(), "setup failure must fail");
    let err = stderr(&output);
    assert!(err.contains("setup command failed"), "stderr={err:?}");
    assert!(
        !err.contains(secret),
        "setup failure diagnostic leaked the expanded secret: {err:?}"
    );
}
