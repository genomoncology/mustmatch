# JSON Subset Matching

Testing JSON subset edge cases.

## Missing Key

```python
from mustmatch.services.comparator import json_match

# Subset has key that actual doesn't have
result = json_match('{"a":1}', '{"a":1,"b":2}', subset=True)
assert not result.matches
```

## Value Mismatch

```python
from mustmatch.services.comparator import json_match

# Key exists but value different
result = json_match('{"a":1,"b":999}', '{"b":2}', subset=True)
assert not result.matches
```

## Nested Value Mismatch

```python
from mustmatch.services.comparator import json_match

# Nested object value mismatch
result = json_match(
    '{"data":{"id":1,"value":42}}',
    '{"data":{"value":999}}',
    subset=True
)
assert not result.matches
```

## Array Subset

```python
from mustmatch.services.comparator import json_match

# All items in expected must exist in actual
result = json_match(
    '[{"id":1},{"id":2},{"id":3}]',
    '[{"id":2}]',
    subset=True
)
assert result.matches

# Item not found
result = json_match(
    '[{"id":1},{"id":2}]',
    '[{"id":3}]',
    subset=True
)
assert not result.matches
```

## Primitive Values

```python
from mustmatch.services.comparator import _is_subset

# Primitives use equality
assert _is_subset(42, 42)
assert not _is_subset(42, 99)
assert _is_subset("hello", "hello")
assert not _is_subset("hello", "goodbye")
```

## Complex Array Subset

```python
from mustmatch.services.comparator import json_match

# Array of objects with subset
result = json_match(
    '[{"id":1,"name":"Alice","age":30},{"id":2,"name":"Bob","age":25}]',
    '[{"id":1,"name":"Alice"}]',
    subset=True
)
assert result.matches

# Array item value mismatch
result = json_match(
    '[{"id":1,"name":"Alice"}]',
    '[{"id":1,"name":"Bob"}]',
    subset=True
)
assert not result.matches
```
