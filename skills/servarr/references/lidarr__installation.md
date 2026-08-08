---
title: Lidarr Installation
description: Instructions and Guides for Installation of Lidarr
tags:
  - lidarr
  - docker
  - installation
  - guide
  - scripts
  - setup
---

# By Platform

[:fontawesome-brands-windows:](installation/windows.md)&nbsp;&nbsp;&nbsp;&nbsp;[:fontawesome-brands-linux:](installation/linux.md)&nbsp;&nbsp;&nbsp;&nbsp;[:fontawesome-brands-apple:](installation/macos.md)&nbsp;&nbsp;&nbsp;&nbsp;[:fontawesome-brands-freebsd:](installation/freebsd.md)&nbsp;&nbsp;&nbsp;&nbsp;[:fontawesome-brands-docker:](installation/docker.md)

# Recommended Guides

- [Setup Reverse Proxy *Complete guide for reverse proxy setup with Nginx or Apache*](installation/reverse-proxy.md)
{.links-list}

# Post-install configuration

Small configuration tweaks that apply regardless of platform. For installation itself, use the platform links above.

## Disable browser-on-startup

{#disable-browser-launch}

By default Lidarr opens a browser window to its UI when it starts. Three ways to turn that off (pick whichever fits your setup):

- **Settings UI:** on most platforms, Settings → General has a **Launch Browser on Start** checkbox. Uncheck it and save. The checkbox isn't present on every platform (notably headless server builds), in which case use one of the options below.
- **Command-line flag:** add `-nobrowser` (Linux/macOS) or `/nobrowser` (Windows) to the Lidarr invocation. For systemd services, add the flag to the `ExecStart=` line in the unit file; for Windows services, edit the service command via `sc config` or directly in the registry. Docker containers never open a browser, so this flag is irrelevant there.
- **Config file:** stop Lidarr, open `config.xml` in the [AppData directory](appdata-directory.md), and set `<LaunchBrowser>False</LaunchBrowser>`. Start Lidarr.

Pick one. They don't stack.
