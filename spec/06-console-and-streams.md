# Console examples and streams

A `console mustmatch` block documents a session the way a reader would see it in
a terminal: lines starting with `$ ` are commands, and the lines beneath each
command are the output the runner checks (as a substring). No `| mustmatch` pipe
is needed — the block class is itself the assertion.

## A console session

Each `$ ` line is run; the lines under it must appear in its output.

```console mustmatch
$ printf 'console ok\n'
console ok
```

Several commands can share one block.

```console mustmatch
$ printf 'first\n'
first
$ printf 'second\n'
second
```

## Expecting a non-zero exit

`exit=` states the exit code the command must return. A command with no expected
output lines is asserted on its exit code alone.

```console mustmatch exit=1
$ false
```

## Selecting a stream

`stream=stderr` checks the command's standard error instead of standard output.

```console mustmatch stream=stderr
$ sh -c 'printf "deprecation warning\n" >&2'
deprecation warning
```

## Timeouts

A block may cap its own run time with `timeout=SECONDS` (overriding the runner's
default). It is a per-block guard against a hung command; a block that exceeds it
fails with a timeout error.

```console mustmatch timeout=5
$ printf 'fast enough\n'
fast enough
```
