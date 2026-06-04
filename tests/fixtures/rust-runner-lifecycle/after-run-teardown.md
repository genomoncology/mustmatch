# After-Run Teardown Fixture

This fixture writes suite and file body sentinels during a successful document run. Suite and file teardown hooks clean those files after the runner exits.

## Successful document leaves cleanup to suite and file teardown

The document body creates the files that suite and file teardown remove after the run.

```bash
printf 'suite body ran\n' > suite-body.txt
printf 'file body ran\n' > file-body.txt
printf 'teardown sentinels written\n' | mustmatch like "teardown sentinels written"
```
