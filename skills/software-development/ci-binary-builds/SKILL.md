---
name: ci-binary-builds
description: "Build native desktop/server binaries via GitHub Actions when the local machine can't cross-compile. Covers Rust, Go, C/C++, and Node — workflow templates, artifact publishing, and release automation."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [CI, GitHub-Actions, cross-compile, Rust, Go, build, binary, release]
    related_skills: [github, plan, spike]
---

# CI Binary Builds

When you need a Windows/macOS/Linux binary but the local machine lacks the
cross-compilation toolchain (no root, no mingw, no MSVC, wrong platform), use
GitHub Actions to build **natively on the target OS runner** and download the
artifact. This is faster and more reliable than fighting cross-compilers.

## When to use this skill

- User asks to "build for Windows" / "make a Mac app" / "compile and give me the exe"
- Local machine is Linux without `mingw-w64` / no `sudo` / no root
- Local machine is macOS without cross-compilers
- You need release artifacts (zip, exe, dmg, AppImage) for distribution
- A repo has a `Cargo.toml` / `go.mod` / `CMakeLists.txt` / `package.json` but no CI

## Workflow

1. **Clone the repo** (shallow is fine): `git clone --depth 1 <url>`
2. **Check the project type**:
   - `Cargo.toml` → Rust (see below)
   - `go.mod` → Go (`go build` on `ubuntu-latest` / `windows-latest`)
   - `CMakeLists.txt` or `Makefile` → C/C++ (use `cmake` step)
   - `package.json` with `pkg` / `nexe` / `electron-builder` → Node
3. **Create a GitHub Actions workflow** under `.github/workflows/build-<target>.yml`
   - Use `templates/rust-windows-build.yml` as a starting point for Rust
   - Adapt the runner OS, build command, and packaging step for other languages
4. **Push the workflow** to the repo (requires `workflow` scope on the token —
   see Pitfalls below)
5. **Watch the run**: `gh run watch <run-id> -R owner/repo`
6. **Download the artifact**: `gh run download <run-id> -R owner/repo -n <artifact-name>`

## Key decisions

### Runner OS
| Target binary | Runner | Notes |
|---|---|---|
| Windows x64 | `windows-latest` | Native MSVC, no cross-compile needed |
| macOS Universal | `macos-latest` | `rustup target add aarch64-apple-darwin` + lipo |
| Linux x64 | `ubuntu-latest` | Use `manylinux` container for portable Linux binaries |
| Linux ARM64 | `ubuntu-latest` | Need QEMU or cross-compilation crate |

### Release vs Debug
Always build with `--release` (Rust) / `-ldflags="-s -w"` (Go) / `cmake -DCMAKE_BUILD_TYPE=Release` for distributable binaries. Debug builds are 10x larger and unoptimized.

### Packaging
- **Rust**: copy the exe from `target/release/<name>.exe` (+ .dll dependencies if any)
- **Go**: static binary, just zip it
- **Node (pkg)**: single executable, zip it
- **Include web assets**: if the project has a `web/` or `public/` dir, copy it alongside the binary

### Tests
Run `cargo test` / `go test` in the workflow **before** packaging. Use `continue-on-error: true` if tests are known-flaky on CI but the build is the priority.

## Pitfalls

- **`workflow` scope required**: The `gh auth login` OAuth flow grants `gist, read:org, repo` but **not** `workflow`. Without it, `git push` of a workflow file is rejected, AND the Contents API and Git Data API also return `404` for any path under `.github/workflows/`. Fix: `gh auth refresh -h github.com -s workflow`. Verify: `gh auth status` must list `workflow` in Token scopes.
- **`gh auth refresh` device code timeout**: The refresh command prints a one-time code + URL (`https://github.com/login/device`) and waits for the user to validate in their browser. The default foreground timeout (10–30s) is often too short. Run it in **background** with `notify_on_complete=true` to give the user ~2 minutes. Print the code and URL from the process log (`process action=log`) so the user can validate in their own browser. On Hermes Docker: `gh` is at `/opt/data/home/.local/bin/gh` and needs `HOME=/opt/data/home` — background processes don't inherit the user's PATH, so always pass the full path.
- **Contents API 404 for nested new paths**: `PUT /repos/{o}/{r}/contents/.github/workflows/foo.yml` returns `404` when the `.github/workflows/` directory doesn't exist yet on the remote. This is NOT a permissions error — the Contents API cannot create intermediate directories. Use the Git Data API (blob → tree → commit → ref) or just `git push`.
- **Cache key**: Use `hashFiles('**/Cargo.lock')` / `hashFiles('**/go.sum')` in the cache key to invalidate on dependency changes.
- **Artifact retention**: Default is 90 days. Set `retention-days: 30` to avoid filling the artifact quota.
- **Large binaries**: GitHub artifact limit is 10 GB per artifact. For larger builds, use GitHub Releases instead (`gh release create` with the binary as an asset).

## See also

- `templates/rust-windows-build.yml` — ready-to-adapt Rust release build + zip + artifact upload
- The `github` skill for gh CLI auth, repo management, and workflow triggering commands