# Clean Directive Fence Fixture

Directive-bearing shell fences are still ordinary shell blocks for linting. A
valid block with a long enough assertion should pass cleanly.

```bash timeout=5
echo "alphabet soup" | mustmatch like "alphabet soup"
```
