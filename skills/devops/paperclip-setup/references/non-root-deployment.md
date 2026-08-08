# Non-root Paperclip Deployment Reference

## Doctor failure when config paths point to /root/

When running Paperclip as user `paperclip` but config paths still reference `/root/.paperclip/`:

```
✗ Secrets adapter: Could not read secrets key file: EACCES: permission denied,
  open '/root/.paperclip/instances/default/secrets/master.key'
✗ Storage: Local storage directory is not writable: /root/.paperclip/instances/default/data/storage
✗ Log directory: Log directory is not writable: /root/.paperclip/instances/default/logs
```

**Fix:** Update all path fields in `config.json` to `/home/paperclip/.paperclip/...` and recreate dirs.

## npx cache corruption: missing ipaddr.js/lib/

```
Cannot find module '/home/paperclip/.npm/_npx/43414d9b790239bb/node_modules/ipaddr.js/lib/ipaddr.js'
```

The npx cache has `ipaddr.js/ipaddr.min.js` but `package.json` expects `lib/ipaddr.js` as main.

**Fix:**
```bash
mkdir -p /tmp/fix_ipaddr && cd /tmp/fix_ipaddr
npm init -y
npm install ipaddr.js@1.9.1
cp -r node_modules/ipaddr.js/lib ~/.npm/_npx/<hash>/node_modules/ipaddr.js/
chown -R $(whoami) ~/.npm/_npx/<hash>/node_modules/ipaddr.js/
```

## npm binary broken for non-root user

Error when running `npm` as non-root:
```
Error: Cannot find module '../lib/cli.js' at /home/paperclip/.local/bin/npm
```

The `~/.local/bin/npm` is a 54-byte stub script pointing to nonexistent `../lib/cli.js`.

**Fix:**
```bash
ln -sf /usr/local/lib/node_modules/npm/bin/npm-cli.js ~/.local/bin/npm
ln -sf /usr/local/lib/node_modules/npm/bin/npx-cli.js ~/.local/bin/npx
```

## npx recompiles sqlite3 every time

Each `npx paperclipai run` triggers C compilation of sqlite3 (~5 min):
- Two `cc1` processes at 95%+ CPU each
- Compiling `sqlite3.c` (180K+ lines) with `-O3`
- Compilation persists 3-5 minutes depending on CPU

**Fix:** Install globally with `npm install -g paperclipai` so native module compiles once.

## Global install fails: EACCES on ~/.local/lib/

```
npm ERR! Error: EACCES: permission denied, mkdir '/home/paperclip/.local/lib/node_modules/@paperclipai'
```

Caused by `~/.local/lib/` owned by `root:root` (created via `sudo mkdir` during earlier setup steps).

**Fix:**
```bash
chown -R $(whoami):$(whoami) ~/.local/
```
