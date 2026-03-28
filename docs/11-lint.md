# Lint

`mustmatch lint` reports assertion mistakes and shell syntax problems in markdown without executing the code blocks themselves. These examples cover help text, assertion findings, and directive-bearing shell fences.

## Help

```bash
mustmatch --help | mustmatch like "mustmatch lint [OPTIONS] SPEC"
mustmatch --help | mustmatch like "mustmatch lint docs/02-cli-assertions.md"
mustmatch lint --help | mustmatch like "spec"
mustmatch lint --help | mustmatch like "--min-like-len MIN_LIKE_LEN"
mustmatch lint --help | mustmatch like "--json"
```

## Assertion Findings

`mustmatch lint` flags unsupported `mustmatch json` mode and short quoted `mustmatch like` literals.

```bash
tmpdir="$(mktemp -d)"
spec="$tmpdir/spec.md"
python - "$spec" <<'PY'
import sys
with open(sys.argv[1], "w") as f:
    f.write("# Lint Sample\n\n")
    f.write("```bash\n")
    f.write("echo '{\"status\":\"ok\"}' | mustmatch json\n")
    f.write('echo "alpha beta" | mustmatch like "beta"\n')
    f.write("```\n")
PY
if mustmatch lint "$spec" --json > "$tmpdir/result.json"; then
  echo "lint unexpectedly passed"
  exit 1
fi
python - <<'PY' "$tmpdir/result.json"
import json, sys
with open(sys.argv[1], "r") as handle:
    data = json.load(handle)
assert data["status"] == "fail"
assert data["finding_count"] == 2
rules = {finding["rule"] for finding in data["findings"]}
assert rules == {"invalid-mustmatch-mode", "short-like-pattern"}
PY
echo "ok" | mustmatch "ok"
rm -rf "$tmpdir"
```

## Shell Fences With Directives

Shell fences still lint correctly when directives follow the language token.

```bash
tmpdir="$(mktemp -d)"
valid_spec="$tmpdir/valid.md"
invalid_spec="$tmpdir/invalid.md"
python - "$valid_spec" "$invalid_spec" <<'PY'
import sys
with open(sys.argv[1], "w") as f:
    f.write("# Valid Directive Fence\n\n")
    f.write("```bash skip\n")
    f.write('echo "alphabet soup" | mustmatch like "alphabet soup"\n')
    f.write("```\n")
with open(sys.argv[2], "w") as f:
    f.write("# Invalid Directive Fence\n\n")
    f.write("```bash timeout=5\n")
    f.write("if then\n")
    f.write('  echo "broken"\n')
    f.write("fi\n")
    f.write("```\n")
PY
mustmatch lint "$valid_spec" --json > "$tmpdir/valid.json"
if mustmatch lint "$invalid_spec" --json > "$tmpdir/invalid.json"; then
  echo "lint unexpectedly passed invalid shell syntax"
  exit 1
fi
python - <<'PY' "$tmpdir/valid.json" "$tmpdir/invalid.json"
import json, sys
with open(sys.argv[1]) as f:
    valid = json.load(f)
with open(sys.argv[2]) as f:
    invalid = json.load(f)
assert valid["status"] == "pass"
assert valid["finding_count"] == 0
assert invalid["status"] == "fail"
assert invalid["finding_count"] == 1
assert invalid["findings"][0]["rule"] == "invalid-shell-syntax"
PY
echo "ok" | mustmatch "ok"
rm -rf "$tmpdir"
```
