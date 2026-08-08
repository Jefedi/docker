---
name: linux-server-hardening
description: Security hardening of Linux servers — read-only audit, prioritization (top 3), step-by-step UFW + fail2ban + SSH + kernel sysctl setup with user validation between each step.
---

# Linux Server Hardening

## When to use
- The user asks to "sécuriser le serveur", "hardening", "firewall", "fail2ban", or references the guide `How-To-Secure-A-Linux-Server` (imthenachoman).
- The user provides a link to a security guide and asks you to compare/apply it.

## Workflow

### Phase 0: Read the Full External Guide (if applicable)

When the user links an external security guide (e.g. imthenachoman/How-To-Secure-A-Linux-Server), **read ALL content files**, not just the README. Extract every linked `.md` file from the repo (README.md, dedicated files like `linux-kernel-sysctl-hardening.md`, `nginx.md`, etc.) using `web_extract(urls=[...])` on the raw GitHub URLs. The user explicitly wants: *"tu lis vraiment tout ce qui est proposé dans la doc"* — all of it, not just the summary.

### Phase 1: Read-Only Audit
Before recommending anything, audit the current system state. Run these checks in parallel:

```bash
# SSH config
sshd -T | grep -E '(permitrootlogin|passwordauthentication|pubkeyauthentication|allowgroups|kexalgorithms|ciphers|macs|loglevel|x11forwarding|allowtcpforwarding|clientalive|maxauthtries|logingracetime|permitempty|challengeresponse)'
grep -vE '^#|^$' /etc/ssh/sshd_config

# Firewall
ufw status verbose  # if installed
iptables -L -n --line-numbers
ip6tables -L -n | head -10

# fail2ban
fail2ban-client status 2>/dev/null || echo "not installed"

# Kernel sysctl
sysctl fs.protected_hardlinks fs.protected_symlinks fs.suid_dumpable
sysctl kernel.randomize_va_space kernel.kptr_restrict kernel.sysrq
sysctl net.ipv4.ip_forward net.ipv4.conf.all.rp_filter
sysctl net.ipv4.conf.all.accept_redirects net.ipv4.conf.all.send_redirects
sysctl net.ipv4.tcp_syncookies net.ipv4.conf.all.log_martians
sysctl net.ipv4.conf.all.accept_source_route

# Updates
dpkg -l unattended-upgrades 2>/dev/null | tail -1
cat /etc/apt/apt.conf.d/20auto-upgrades 2>/dev/null
systemctl is-active unattended-upgrades 2>/dev/null

# Other security tools
dpkg -l fail2ban ufw firejail libpam-google-authenticator psad apticron logwatch 2>/dev/null | grep ^ii

# Network & services
ss -tlnp
ip -br a
tailscale ip 2>/dev/null || true

# Users
getent group sudo
grep -E 'bash|zsh' /etc/passwd | cut -d: -f1
```

### Phase 2: Prioritize (Top 3)
Present a clear top 3 priorities based on risk. Use this order:

1. **Firewall (UFW + fail2ban)** — highest impact, quickest win
2. **SSH hardening** — everyday attack surface
3. **Kernel sysctl hardening** — defense-in-depth

For each item, show:
- What's missing vs the guide/recommendation
- Why it matters (practical risk, not theoretical)
- What the fix would look like (without executing unless user approves)

### Phase 3: Step-by-Step Execution
**CRITICAL**: Each step must be explicitly approved by the user before executing. The user's rule: "chaque action doit être demandée par moi-même."

After each substep:
- Report what was done
- Show the result/verification
- Wait for user go-ahead before next step

### Phase 4: Verification
After each change, verify it's working:
- `sudo ufw status verbose` for firewall rules
- `sudo fail2ban-client status sshd` for bans
- Check SSH still works (new terminal / user confirmation)
- Show banned IPs as proof of effectiveness
- For endlessh tarpit: `ss -tlnp | grep endless` + `ssh -p 22 user@localhost` should timeout

### Phase 4b (optional): SSH Tarpit (endlessh)

When the user wants to move SSH to a non-standard port and leave a honeypot/tarpit on port 22:

#### Port migration sequence (CRITICAL — do not deviate)
1. Add the new SSH port **alongside** port 22 in sshd_config (`Port 22\nPort <new>`)
2. `systemctl restart ssh`
3. Verify both ports listen (`ss -tlnp | grep sshd`)
4. **Test** new port locally (`echo | nc 127.0.0.1 <new>` shows SSH banner)
5. Update UFW: add `limit` for new port, change port 22 from LIMIT to ALLOW
6. Remove port 22 from sshd_config, restart SSH
7. Verify SSH now only on new port
8. Install and start endlessh on port 22

#### endlessh setup (Debian-specific)

```bash
# Install
apt install endlessh

# Grant capability to bind ports <1024
setcap 'cap_net_bind_service=+ep' /usr/bin/endlessh

# Edit /usr/lib/systemd/system/endlessh.service:
#   - Uncomment AmbientCapabilities=CAP_NET_BIND_SERVICE
#   - Comment PrivateUsers=true
#   - Set ExecStart with CLI args (config file is broken on Debian):
#     ExecStart=/usr/bin/endlessh -p 22 -d 10000000 -m 4096 -l 255 -s

systemctl daemon-reload
systemctl start endlessh
```

**Known issue — Debian config format:** The Debian package (endlessh 1.1-5.1) does NOT accept config directives like `port 22`. It errors with "Unknown option 'port'". **Use CLI flags in ExecStart instead.** Keep `/etc/endlessh/config` empty.

**Parameters:** `-p` port, `-d` delay in microseconds (10,000,000 = 10s/char), `-m` max clients, `-l` banner line length (max 255), `-s` syslog.

### SSH User Access Control

```bash
sudo groupadd sshusers
sudo usermod -a -G sshusers root
echo "AllowGroups sshusers" | sudo tee -a /etc/ssh/sshd_config
```

**Pitfall:** Ask the user before setting `PermitRootLogin no`. On single-user VPS with Docker running as root, this causes more friction than benefit.

### SSH AllowTcpForwarding

Setting `AllowTcpForwarding no` (common in hardening guides) prevents ALL SSH port forwarding, including legitimate use cases like OAuth callback forwarding, tunneling web services, and IDE debuggers. The symptom is `"Remote has rejected the forwarded connection"`. **Ask the user** if they need port forwarding before setting this.

### /proc hidepid

```bash
echo "proc    /proc    proc    defaults,hidepid=2    0    0" | sudo tee -a /etc/fstab
sudo mount -o remount,hidepid=2 /proc
```

#### Verification
```bash
ss -tlnp | grep endless                    # *:22
ssh -p 22 user@localhost                    # Times out during banner exchange
ssh -p <new-port> user@localhost            # Instant response
```

### Presentation style (user preference)
- Use **before/after tables** for changes
- ✅/❌ markers for what's OK/missing
- Concise bullet lists, not prose paragraphs
- After each phase, ask explicitly: "C'est bon pour toi ? On continue ?"

## Practical Adaptations for Docker Hosts

### UFW + Docker compatibility
Docker adds iptables rules that **bypass UFW**. A published container port can be accessible even if UFW denies it inbound. Mitigations:
- Use `--network host` for sensitive services (iptables then applies normally)
- Or configure `/etc/docker/daemon.json` with `"iptables": false` (breaks Docker networking — not recommended)
- The simplest practical approach: trust Docker's own iptables management for containers, use UFW for the host OS

### Outgoing traffic policy
- **`deny outgoing`** (as recommended by imthenachoman guide) is aggressive and **breaks**: Docker image pulls, apt updates, git operations, Tailscale, Hermes API calls, and most web services.
- **Default: `allow outgoing`** on VPS/Docker hosts. Lock down outgoing only if the user explicitly asks for it and is willing to maintain the whitelist.

### Tailscale
Always add Tailscale subnet (`100.64.0.0/10`) to fail2ban ignoreip to avoid banning internal/admin traffic.

## Common Pitfalls
- 🚩 **Forgetting to add `ufw limit` instead of `ufw allow` for SSH** — `limit` rate-limits (6/30s), `allow` leaves it wide open.
- 🚩 **Enabling UFW before allowing SSH** — lock yourself out. Always `ufw limit 22/tcp` BEFORE `ufw --force enable`.
- 🚩 **`deny outgoing` on Docker hosts without whitelisting** — Docker pulls will fail silently. User will only notice when containers can't update.
- 🚩 **fail2ban systemd socket timing** — `sudo systemctl restart fail2ban` then immediately `status` can give "Failed to access socket path". Just wait 1-2 seconds.
- 🚩 **PSAD + UFW LOG rules** — if adding LOG rules to `/etc/ufw/before.rules`, add them BEFORE the `*filter` section ends with `COMMIT`. Test with `sudo ufw reload`.

## Files

- `references/security-audit-commands.md` — exact audit commands with expected output examples
