# My Project

## Installation

Check Python is installed:

```bash
python3 --version | mustmatch like "Python"
```

## Basic Usage

Test help output:

```bash skip
echo "Usage: myapp [OPTIONS]" | mustmatch like "Usage:"
```

## JSON API

Test JSON response:

```bash
echo '{"status":"ok","version":"1.0"}' | \
    mustmatch like '{"status":"ok"}'
```

## Error Handling

Verify no errors appear:

```bash
echo "Operation completed successfully" | \
    mustmatch not like "error"
```
