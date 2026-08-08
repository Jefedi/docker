---
name: docker-fork-autobuild
title: Fork & Auto-Build Docker Images to GHCR
description: "Fork an upstream Docker image repo and auto-build to GitHub Container Registry on every upstream release. Eliminates the lag between upstream app releases and official Docker image updates. Drop-in image replacement — zero config change for the end user."
tags: [docker, ghcr, github-actions, fork, autobuild, ci]
metadata:
  hermes:
    related_skills: [github, new-service-onboarding]
---

# Fork & Auto-Build Docker Images to GHCR

When the official Docker image for a project lags behind the upstream app releases (common with community-maintained Docker wrappers like CrazyMax's images), fork the Docker repo and set up two GitHub Actions workflows to auto-build and push to GHCR.

## When to Use

- Upstream app releases new versions but the Docker image repo takes weeks to catch up
- You self-host with Docker and need timely updates
- The Docker image repo is maintained by a third party (not the app author)
- You want to control the build cadence without waiting for the maintainer

## Workflow

### 1. Fork the Docker image repo

```bash
gh repo fork anonaddy/docker --clone=false
gh repo clone Jefedi/docker /tmp/docker-fork -- --depth=1
```

### 2. Understand the Dockerfile version mechanism

Most Docker image repos use a build ARG to pin the upstream version:

```dockerfile
ARG ANONADDY_VERSION=1.6.4
# ...
RUN git fetch --depth 1 origin "v${ANONADDY_VERSION}" && git checkout -q FETCH_HEAD
```

The autobuild pattern: detect new upstream releases → bump the ARG → tag → build.

### 3. Create `sync-upstream.yml` workflow

Polls the upstream app repo for new releases every 6 hours. On new release: updates the Dockerfile ARG, commits, and creates a tag `v{VERSION}-r`.

See `templates/sync-upstream.yml` for the full workflow file.

Key steps:
- `gh release view --repo <upstream/repo> --json tagName -q .tagName` to get latest release
- Compare against the ARG value in the Dockerfile
- `sed -i` to bump the version
- Commit + tag + push (needs `permissions: contents: write`)

### 4. Create/replace `build.yml` workflow

Builds the multi-arch image and pushes to GHCR. Triggered by pushes to master and tags matching `v*-r`.

See `templates/build-ghcr.yml` for the full workflow file.

Key elements:
- `permissions: contents: read, packages: write`
- Login to GHCR with `${{ secrets.GITHUB_TOKEN }}` (no extra secrets needed)
- `docker/metadata-action` for tag generation: `type=match,pattern=v(.*)-r,group=1` + `type=raw,value=latest`
- `docker/build-push-action` with `platforms: linux/amd64,linux/arm64`
- GHA cache (`cache-from: type=gha`, `cache-to: type=gha,mode=max`)

### 5. Clean up unnecessary workflows

Remove workflows from the fork that reference external secrets or reusable workflows from the original maintainer (e.g. `labels.yml`, `zizmor.yml`, `test.yml`, dependabot configs that bump actions you don't use).

### 6. Update the user's docker-compose

Change only the image line:
```yaml
# Before
image: anonaddy/anonaddy:latest
# After
image: ghcr.io/jefedi/anonaddy:latest
```

**Zero other changes** — same env vars, volumes, ports, network. The image is functionally identical (same Dockerfile, same rootfs).

## Pitfalls

- **`gho_` OAuth token cannot push workflow files**: The default `gh auth login` token (`gho_…`) lacks the `workflow` scope. ALL GitHub API endpoints (contents PUT, git trees POST, git refs PATCH) return **404 Not Found** (not 403) for paths under `.github/workflows/`. Non-workflow files work fine. Fix: `gh auth refresh -h github.com -s workflow` (requires browser) or use a classic PAT with `repo` scope, or have the user create workflow files via the GitHub web UI.
- **Git Data API tree 404**: When using `POST /git/trees` with a `base_tree` SHA, ensure the SHA is from the fork's own HEAD, not the upstream's. Re-fetch `git/refs/heads/master` → `git/commits/{sha}` → `tree.sha` on the fork before constructing the payload.
- **GHCR visibility**: New GHCR packages are private by default. Go to the package settings on GitHub to make it public (or pull with authentication).
- **Multi-arch build time**: Building `linux/amd64,linux/arm64` takes 20-40 min with QEMU emulation for PHP/Node images. Use GHA cache to speed up subsequent builds.
- **Tag pattern consistency**: The `sync-upstream` workflow must create tags matching the `build` workflow's `on.push.tags` pattern. If sync creates `v1.7.0-r` and build expects `v*`, the build won't trigger.
- **Removing workflows that are reusable workflow references**: The original `build.yml` may use `docker/github-builder/.github/workflows/bake.yml@<sha>` — this requires Docker Hub secrets that the fork doesn't have. Replace with a standalone build workflow.

## Reference Files

- `templates/sync-upstream.yml` — ready-to-adapt upstream release polling workflow
- `templates/build-ghcr.yml` — ready-to-adapt multi-arch GHCR build workflow