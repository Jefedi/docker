# Security Audit Commands Reference

## endlessh SSH Tarpit Setup

```bash
# Install
apt install endlessh

# Grant low-port capability
setcap 'cap_net_bind_service=+ep' /usr/bin/endlessh

# Enable low-port binding in service
sed -i 's/^#AmbientCapabilities=CAP_NET_BIND_SERVICE/AmbientCapabilities=CAP_NET_BIND_SERVICE/' /usr/lib/systemd/system/endlessh.service
sed -i 's/^PrivateUsers=true/#PrivateUsers=true/' /usr/lib/systemd/system/endlessh.service

# Replace ExecStart line to use CLI args (Debian config format is broken):
sed -i 's|ExecStart=/usr/bin/endlessh$|ExecStart=/usr/bin/endlessh -p 22 -d 10000000 -m 4096 -l 255 -s|' /usr/lib/systemd/system/endlessh.service

systemctl daemon-reload
systemctl reset-failed endlessh  # if previously failed
systemctl start endlessh

# Verify
ss -tlnp | grep endless
```

## SSH Port Migration

```bash
# 1. Add new port alongside old
sed -i 's/^#\?Port 22/Port 22\nPort <new-port>/' /etc/ssh/sshd_config
sshd -t && systemctl restart ssh
ss -tlnp | grep sshd

# 2. Test new port locally
echo | nc 127.0.0.1 <new-port> | head -1
# Should show: SSH-2.0-OpenSSH_...

# 3. Remove old port from SSH
sed -i '/^Port 22$/d' /etc/ssh/sshd_config
sshd -t && systemctl restart ssh
ss -tlnp | grep sshd  # Should only show <new-port>
```

## SSH Hardening Checks

```bash
# Full non-default SSH config
sshd -T | grep -E '(permitrootlogin|passwordauthentication|pubkeyauthentication|allowgroups|kexalgorithms|ciphers|macs|loglevel|x11forwarding|allowtcpforwarding|clientalive|maxauthtries|logingracetime|permitempty|challengeresponse)'

# Raw config file
grep -vE '^#|^$' /etc/ssh/sshd_config

# SSH version
ssh -V

# Drop-in configs
ls -la /etc/ssh/sshd_config.d/
cat /etc/ssh/sshd_config.d/*.conf

# SSH port
grep -i "^port " /etc/ssh/sshd_config
```

## Firewall

```bash
# UFW
ufw status verbose
ufw status numbered

# Raw iptables
iptables -L -n --line-numbers
ip6tables -L -n | head -10

# Docker-specific chains
iptables -L DOCKER -n --line-numbers 2>/dev/null
iptables -L DOCKER-USER -n --line-numbers 2>/dev/null

# Listening services
ss -tlnp
```

## fail2ban

```bash
fail2ban-client status          # list jails
fail2ban-client status sshd     # jail details (banned IPs, failures)

# Config files
cat /etc/fail2ban/jail.local 2>/dev/null
ls /etc/fail2ban/jail.d/
```

## Kernel sysctl

```bash
# Protection
sysctl fs.protected_hardlinks
sysctl fs.protected_symlinks
sysctl fs.suid_dumpable

# ASLR
sysctl kernel.randomize_va_space

# Pointer hiding
sysctl kernel.kptr_restrict

# SysRq
sysctl kernel.sysrq

# Network hardening
sysctl net.ipv4.conf.all.rp_filter
sysctl net.ipv4.conf.all.accept_redirects
sysctl net.ipv4.conf.all.send_redirects
sysctl net.ipv4.conf.all.log_martians
sysctl net.ipv4.conf.all.accept_source_route
sysctl net.ipv4.ip_forward
sysctl net.ipv4.tcp_syncookies
sysctl net.ipv4.icmp_echo_ignore_broadcasts
sysctl net.ipv4.icmp_ignore_bogus_error_responses

# IPv6
sysctl net.ipv6.conf.all.disable_ipv6

# Config files
ls -la /etc/sysctl.d/
cat /etc/sysctl.conf 2>/dev/null
```

## Package & Updates

```bash
# Check tools
dpkg -l unattended-upgrades fail2ban ufw firejail libpam-google-authenticator psad apticron logwatch 2>/dev/null | grep ^ii

# Auto-update config
cat /etc/apt/apt.conf.d/20auto-upgrades 2>/dev/null
systemctl is-active unattended-upgrades

# pwquality
grep pam_pwquality /etc/pam.d/common-password 2>/dev/null
```

## Users & Sudo

```bash
# Users with shell
grep -E 'bash|zsh' /etc/passwd | cut -d: -f1

# Sudo group members
getent group sudo

# su restriction
dpkg-statoverride --list 2>/dev/null | grep /bin/su
```

## System

```bash
# hidepid in /proc
grep hidepid /etc/fstab 2>/dev/null

# Docker version
docker info --format '{{.ServerVersion}}' 2>/dev/null
docker network ls 2>/dev/null
cat /etc/docker/daemon.json 2>/dev/null || echo "no daemon.json"

# Tailscale
tailscale ip 2>/dev/null || true

# Network interfaces
ip -br a
```

## Expected "Green" Values

| Setting | Expected value | Meaning |
|---------|---------------|---------|
| `PermitRootLogin` | `no` or `prohibit-password` | No root password login |
| `PasswordAuthentication` | `no` | Keys only |
| `X11Forwarding` | `no` | No X11 tunnel |
| `AllowTcpForwarding` | `no` | No port forwarding |
| `LogLevel` | `VERBOSE` | Detailed logging |
| `ClientAliveInterval` | `15` or `300` | Drop dead sessions |
| `ClientAliveCountMax` | `3` | Max keepalive probes |
| `kernel.kptr_restrict` | `2` | Hide kernel pointers |
| `kernel.sysrq` | `0` | Disable SysRq |
| `net.ipv4.conf.all.rp_filter` | `1` | Anti-spoofing |
| `net.ipv4.conf.all.send_redirects` | `0` | Don't send redirects |
| `net.ipv4.conf.all.log_martians` | `1` | Log suspicious packets |
| `fs.protected_hardlinks` | `1` | Hardlink protection |
| `fs.protected_symlinks` | `1` | Symlink protection |
| `kernel.randomize_va_space` | `2` | Full ASLR |
| `ufw default incoming` | `deny` | Block inbound |
| `ufw status` | `active` | Firewall on |
| fail2ban jail sshd | `enabled=true` | Brute-force protection |
