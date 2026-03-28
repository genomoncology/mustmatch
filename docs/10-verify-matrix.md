# Verify Matrix

`mustmatch verify-matrix` checks proof-matrix file references without needing the Rust extension at CLI import time. These examples cover help text, valid in-repo references, and invalid or missing references.

## Import And Help

This smoke test copies the pure-Python CLI package files into a temporary package without `_core` and imports `mustmatch.cli` from there.

```bash
tmpdir="$(mktemp -d)"
mkdir -p "$tmpdir/mustmatch"
cp ../src/mustmatch/__init__.py ../src/mustmatch/cli.py ../src/mustmatch/runtime.py ../src/mustmatch/version.py "$tmpdir/mustmatch/"
PYTHONPATH="$tmpdir" python -c 'import mustmatch.cli; print("ok")' | mustmatch "ok"
mustmatch --help | mustmatch like "mustmatch verify-matrix [OPTIONS] DESIGN"
mustmatch --help | mustmatch like "mustmatch verify-matrix .march/design-final.md --repo-root ."
mustmatch verify-matrix --help | mustmatch like "design"
mustmatch verify-matrix --help | mustmatch like "--repo-root REPO_ROOT"
mustmatch verify-matrix --help | mustmatch like "--json"
rm -rf "$tmpdir"
```

## Valid References

Repo-relative references inside table rows resolve successfully, including files under `src/` and files at the repo root.

```bash
tmpdir="$(mktemp -d)"
design="$tmpdir/design.md"
cat > "$design" <<'EOF'
| behavior | verification command | spec / artifact |
| --- | --- | --- |
| valid source file | `echo ok` | `src/mustmatch/cli.py` |
| valid repo-root file | `echo ok` | `README.md` |
EOF
mustmatch verify-matrix "$design" --repo-root .. --json > "$tmpdir/result.json"
python - <<'PY' "$tmpdir/result.json"
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = json.load(handle)

assert data["status"] == "pass"
assert data["failure_count"] == 0
assert data["references_checked"] == 2
statuses = {item["reference"]: item["status"] for item in data["results"]}
assert statuses == {
    "src/mustmatch/cli.py": "ok",
    "README.md": "ok",
}
PY
echo "ok" | mustmatch "ok"
rm -rf "$tmpdir"
```

## Invalid And Missing References

Absolute and repo-escaping references are rejected as `invalid`, while unresolved in-repo files are reported as `missing`.

```bash
tmpdir="$(mktemp -d)"
design="$tmpdir/design.md"
cat > "$design" <<'EOF'
| behavior | verification command | spec / artifact |
| --- | --- | --- |
| repo escape is rejected | `echo ok` | `../../outside.py` |
| missing repo file is reported | `echo ok` | `src/mustmatch/does_not_exist.py` |
EOF
if mustmatch verify-matrix "$design" --repo-root .. --json > "$tmpdir/result.json"; then
  echo "verify-matrix unexpectedly passed"
  exit 1
fi
python - <<'PY' "$tmpdir/result.json"
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = json.load(handle)

assert data["status"] == "fail"
assert data["failure_count"] == 2
statuses = {item["reference"]: item["status"] for item in data["results"]}
assert statuses == {
    "../../outside.py": "invalid",
    "src/mustmatch/does_not_exist.py": "missing",
}
PY
echo "ok" | mustmatch "ok"
rm -rf "$tmpdir"
```
