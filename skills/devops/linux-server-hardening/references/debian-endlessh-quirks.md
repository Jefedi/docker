# Debian endlessh 1.1 Package Quirks

The Debian package `endlessh` (v1.1-5.1 as of Debian 13 "Trixie") has significant differences from upstream:

## Config file format
The config file `/etc/endlessh/config` does **NOT** support these directives:
- `port`, `delay`, `maxclients`, `maxlength`, `loglevel`

Instead, the file format is **unknown/broken** in this version. Any content in the file causes:
```
Unknown option '<option>'
Missing value
```
and the service exits with code 1.

## Solution: CLI flags in ExecStart
Bypass the config file entirely:
1. Clear the config: `sudo truncate -s 0 /etc/endlessh/config`
2. Set CLI flags directly in the systemd service:
   ```
   ExecStart=/usr/bin/endlessh -p 22 -d 10000000 -m 4096 -l 255 -s
   ```

## Valid CLI flags
| Flag | Description | Default |
|------|-------------|---------|
| `-p INT` | Listening port | 2222 |
| `-d INT` | Message delay in ms | 10000 (10ms) |
| `-m INT` | Max clients | 4096 |
| `-l INT` | Max banner line length (3-255) | 32 |
| `-s` | Log to syslog | off |
| `-v` | Verbose (repeatable) | off |
| `-4` | IPv4 only | both |
| `-6` | IPv6 only | both |

## Binding to port < 1024
Required modifications to `/usr/lib/systemd/system/endlessh.service`:
```bash
sudo setcap 'cap_net_bind_service=+ep' /usr/bin/endlessh
# Uncomment:
sudo sed -i 's/^#AmbientCapabilities=CAP_NET_BIND_SERVICE/AmbientCapabilities=CAP_NET_BIND_SERVICE/' /usr/lib/systemd/system/endlessh.service
# Comment:
sudo sed -i 's/^PrivateUsers=true/#PrivateUsers=true/' /usr/lib/systemd/system/endlessh.service
```
Then `sudo systemctl daemon-reload`.

## Tarpit timing
- `-d 10000000` = 10 **seconds** per character (10000000 microseconds = 10,000 ms)
- SSH client typically times out after ~30s of banner exchange → attacker gets ~3 characters
- `-d 3000000` = 3 seconds per character (more moderate)
