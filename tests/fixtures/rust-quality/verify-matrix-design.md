# Verify Matrix Fixture

Only repo-like file references in proof-matrix table rows should be checked.
Routes, shell commands, and environment-expanded pseudo-paths are examples, not
repo files.

| behavior | verification command | spec / artifact |
| --- | --- | --- |
| existing root file resolves | `make spec` | `README.md` |
| missing repo file is reported | `make spec` | `docs/does-not-exist.md` |
| HTTP route is not a repo path | `curl https://service.example/v1/resource` | `https://service.example/v1/resource` |
| shell command is not a repo path | `printf ok && rm -rf output` | `printf ok && rm -rf output` |
| env-expanded value is not a repo path | `echo $REPORT_PATH` | `$REPORT_PATH` |
