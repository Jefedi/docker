#!/usr/bin/env bash
# gh-install.sh — Install GitHub CLI on any platform
# Usage: source scripts/gh-install.sh  (or bash scripts/gh-install.sh)
# Sources gh-env.sh after install to re-detect auth status.

set -euo pipefail

install_gh() {
    if command -v gh &>/dev/null; then
        echo "✓ gh already installed: $(gh --version 2>/dev/null | head -1)"
        return 0
    fi

    echo "→ Installing GitHub CLI..."

    # Detect package manager
    if command -v apt-get &>/dev/null; then
        apt-get update -qq && apt-get install -y -qq gh
    elif command -v brew &>/dev/null; then
        brew install gh
    elif command -v winget &>/dev/null; then
        winget install --silent GitHub.cli
    elif command -v dnf &>/dev/null; then
        dnf install -y gh
    elif command -v yum &>/dev/null; then
        yum install -y gh
    elif command -v pacman &>/dev/null; then
        pacman -S --noconfirm github-cli
    else
        # Manual tarball install as fallback
        local version
        version=$(curl -s https://api.github.com/repos/cli/cli/releases/latest | grep tag_name | cut -d'"' -f4)
        local url="https://github.com/cli/cli/releases/download/${version}/gh_${version#v}_linux_amd64.tar.gz"
        curl -sL "$url" | tar xz -C /tmp
        cp /tmp/gh_*/bin/gh /usr/local/bin/
        cp -r /tmp/gh_*/share/man/man1/* /usr/local/share/man/man1/ 2>/dev/null || true
        rm -rf /tmp/gh_*
    fi

    if command -v gh &>/dev/null; then
        echo "✓ gh installed: $(gh --version 2>/dev/null | head -1)"
    else
        echo "✗ Failed to install gh"
        return 1
    fi
}

install_gh
