---
name: docker-service-migration
description: >-
  Safely migrate Docker services between hosts while preserving shared NFS
  storage with hardlink support. Covers *arr stacks, Gluetun VPN services,
  and any containerized workload backed by remote NAS storage.
category: devops
triggers:
  - user asks to move services from host A to host B
  - user asks to consolidate services onto one machine
  - user says "migrer" or "déplacer" services
  - migration involving NAS/NFS storage that must preserve hardlinks
tags: [migration, docker, nfs, hardlink, homelab, media-stack]
---

# Docker Service Migration Between Hosts (with NFS Storage)

## When to Load This Skill

Load when the user needs to move existing Docker services from one host to another, especially when:
- The storage lives on a NAS and is accessed via NFS on both hosts
- Hardlinks must be preserved (critical for *arr/qbit/media workflows)
- Zero data loss is required
- Both stacks must be able to run in parallel during validation

## Migration Methodology

### Phase 1: Understand the Current Setup

Before touching anything, map out:
- Source host compose files, .env, and all service configs
- Target host filesystem (what's already there, what mounts exist)
- NFS mount points and export configuration on the NAS
- Network topology (VPN containers like Gluetun, network_mode relationships)
- Cross-service dependencies (Janitorr → Jellyfin + *arr)

### Phase 2: Backup Everything (CRITICAL)

On the **source host**, before any change:
1. Tar up all config directories
2. Copy compose.yaml and .env to a safe location
3. For VPN services (Gluetun), export the WireGuard config and note the forwarded port
4. Verify backups are readable and non-empty (\>1KB)

### Phase 3: Verify the Target Host's NFS Mount

On the **target host**, before deploying anything:
1. Confirm the NFS mount is active (`df -h`, `mount | grep nfs`)
2. Verify the full directory tree is accessible
3. **Test hardlinks over NFS** — create a test file, hardlink it across directories, check inode numbers match

If inodes differ, hardlinks will NOT work. Fix NFS export options first (`nohide`, `crossmnt`, NFSv4 recommended).

### Phase 4: Create Target Compose Files

Key adaptation rules when migrating compose files:
1. Replace source bind paths with target equivalents (e.g., `/volume1/media center/media-center:/data` → `/mnt/nfs-mount:/data`)
2. Bind VPN service ports to `127.0.0.1:` on the target if it uses a reverse proxy (Pangolin, Nginx Proxy Manager), vs binding to `0.0.0.0` on source
3. Keep the same network mode pattern (`service:gluetun` etc.)
4. Keep the same image versions (lock versions, don't auto-upgrade during migration)
5. Keep the same PUID/PGID
6. Cross-service configs (Janitorr's `application.yml`) may need URL updates from source IP to localhost

### Phase 5: Deploy One Service at a Time

1. Pull all images first
2. Start Gluetun (or VPN service) alone → verify VPN connection + port forwarding
3. Start services one by one, verifying after each:
   - Container is running (`docker ps`)
   - Web UI responds (`curl http://127.0.0.1:<port>`)
   - Logs are clean (`docker logs --tail 20`)
4. After all services are up, verify integrations:
   - Sonarr/Radarr root folders point to valid paths
   - *arr can see existing media
   - qBittorrent shows existing torrents
   - Cross-service communication works (e.g., Janitorr can reach both Jellyfin and *arr)

### Phase 6: Validation Period

**Do NOT shut down the source host until:**
- At least 48 hours of normal operation on target
- A new download/download cycle successfully completes
- Hardlinks verify after real usage
- User confirms everything works

### Rollback Strategy

The two stacks can run in parallel since they point to the same NFS storage.
For any failing service:
1. Stop it on the target
2. Restart it on the source
3. Investigate the issue before retrying

## NFS + Hardlink Considerations

- **Same mount required**: Source and target of a hardlink must be on the same NFS mount. Don't mount subdirectories separately.
- **NFSv4 recommended**: Better hardlink support than v3.
- **Export flags on NAS**: `nohide` and `crossmnt` if the export contains sub-mounts.
- **Permissions**: PUID/PGID must match between host and NAS filesystem owners (or use idmap).
- **Test before trusting**: `touch file1; ln file1 file2; ls -li file1 file2` — inode numbers must be identical.

## Pitfalls

- **Systemd mount timeout**: If NFS mount uses `_netdev` in fstab, Docker may start before NFS is mounted. Add `Requires=mnt-nfs-mount.mount` to `docker.service` drop-in.
- **Port forwarding changes**: VPN port forwarding may change after Gluetun restart. qBittorrent's auto-update command must be configured correctly.
- **Janitorr on network_mode: host**: This container needs access to both VPN'd services (via localhost bound ports) and non-VPN services (Jellyfin). Verify all target ports are reachable.
- **Cross-seed BT_backup path**: The path to qBittorrent's `BT_backup` directory must be exact, including the nested `qBittorrent/BT_backup` subdirectories.
- **Don't upgrade during migration**: Use the same image versions on target as source. Upgrade separately, later.

## Related Skills
- `new-service-onboarding` — for deploying brand-new services (complementary; this skill is for migration)
- `infrastructure-doctor` — run after migration to verify health
- `homelab-mesh-connect` — for setting up Tailscale/Headscale on the target if needed

## References
- `references/media-stack-migration-jefe-2026-05-31.md` — full session transcript with complete compose files, Jefe-specific paths, and the exact prompt generated for Claude Code to execute the migration.
