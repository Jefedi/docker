# Getting Full Stack Traces from Opaque CLI Tools

Some CLI tools swallow the real error and only show `err.message` (not `err.stack`), making it impossible to locate the actual failure point. This ref documents how to force full stack traces from Node.js tools with minified/compiled source.

## Signal

The tool prints a vague top-level error like:
```
Paperclip server failed to start.
Invalid URL
```

The error message is too generic to locate the issue. You need the **stack trace**.

## Technique

### 1. Locate the error handler

Search for the string that prefixes the error output in the tool's dist/ directory:

```bash
grep -r "Paperclip server failed" /path/to/tool/dist/ | head -5
```

### 2. Find the `formatError` or equivalent function

```bash
grep -n "function formatError\|formatError(err)" /path/to/tool/dist/index.js | head -5
```

### 3. Patch to return the full stack

The typical pattern is:

```js
function formatError(err) {
  if (err instanceof Error) {
    if (err.message && err.message.trim().length > 0) return err.message;  // ← this hides the stack
    return err.name;
  }
  // ...
}
```

Replace the function body to return the stack instead:

```bash
# Use sed to inject a stack-returning guard at the top
sed -i 's/function formatError(err) {/function formatError(err) { if(err instanceof Error) { return err.stack || err.message; }/' /path/to/tool/dist/index.js
```

This makes the first return statement return `err.stack` instead of `err.message`.

### 4. Re-run the failing command

```bash
DATABASE_URL="postgresql://..." npx toolname run 2>&1
```

Now you'll see the full stack trace:

```
Paperclip server failed to start.
TypeError: Invalid URL
    at new URL (node:internal/url:818:25)
    at parseUrl (node_modules/postgres/src/index.js:545:18)
    at ...
```

### 5. Restore the original

After debugging, revert the patch (or keep it if you're still debugging the same issue):

```bash
# Re-run with original if needed — the patch persists in node_modules
```

The file is in a npx cache directory, so it'll be replaced on next `npx` invocation.

## Variations

### For Python tools with truncated tracebacks

```python
import traceback, sys

def format_error(e):
    return ''.join(traceback.format_exception(type(e), e, e.__traceback__))
```

### For Go binaries with only error strings

Use `GOTRACEBACK=all` environment variable:

```bash
GOTRACEBACK=all ./binary 2>&1
```

### For tools that log to files

```bash
tail -f /path/to/logs/*.log
# or
grep -i error /path/to/logs/*.log | tail -30
```

## Why This Works

- `err.message` typically contains only the error string (e.g. "Invalid URL")
- `err.stack` contains the full traceback showing every call in the chain
- Most CLI tools use a generic `formatError` to keep logs clean
- Patching it temporarily reveals the actual failure origin

## When to Use

- The tool prints a short, unhelpful error message
- Logs don't contain more detail
- The error is deep in a dependency (npm package, library)
- You've already verified config and environment
