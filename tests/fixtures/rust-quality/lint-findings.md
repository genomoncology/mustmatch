# Lint Findings Fixture

This file intentionally contains one example for each lint finding family that the
Rust command must report without executing the shell block.

```bash timeout=5
echo '{"status":"ok"}' | mustmatch json
echo "alpha beta" | mustmatch like "beta"
if then
  echo "broken"
fi
```
