# Test Documentation

## Example 1: Echo

```bash
echo "hello world" | mustmatch like "world"
```

## Example 2: Date Format

```bash
date +%Y-%m-%d | mustmatch '/^\d{4}-\d{2}-\d{2}$/'
```

## Example 3: JSON

```bash
echo '{"status":"ok"}' | mustmatch '{"status":"ok"}'
```
