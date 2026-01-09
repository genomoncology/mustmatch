# Getting Started

## Installation

Install outmatch with pip or uv:

```
pip install outmatch
uv add outmatch
```

## Basic Usage

Verify exact output:

```bash
echo "hello world" | outmatch "hello world"
```

Check output contains a substring:

```bash
echo "version 1.2.3" | outmatch --contains "1.2"
```

Match with regex:

```bash
echo "completed in 42ms" | outmatch --regex 'completed in \d+ms'
```

## JSON Comparison

Compare JSON regardless of field order:

```bash
echo '{"b":2,"a":1}' | outmatch --json '{"a":1,"b":2}'
```

## Handling Volatile Output

Replace timestamps before comparison:

```bash
echo "time: 1.5s" | outmatch --replace '\d+\.\d+s=>TIME' "time: TIME"
```
