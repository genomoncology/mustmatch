# Context Teardown Fixture

This fixture shows that context teardown runs after the final block using that context. The following no-context block observes the cleanup effect directly.

## Context body can use setup state

The context block reads setup state and writes a body sentinel in the context cwd.

```bash context=cleanup
printf 'context body ran\n' > context-body.txt
cat context-setup.txt | mustmatch like "context=ready"
```

## Context teardown removes body sentinel

After the last `cleanup` context block, the teardown hook removes the body sentinel before ordinary no-context blocks continue.

```bash
ls context-body.txt 2>/dev/null | mustmatch not like "context-body.txt"
```
