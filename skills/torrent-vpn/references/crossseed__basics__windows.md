---
id: windows
sidebar_position: 1
title: Windows Quickstart
---

If your torrent client runs on Windows, install `cross-seed` natively with
`npm`. Do not run `cross-seed` in Docker Desktop for Windows if you want to use
linking, partial matching, or data-based matching. Docker runs in a Linux VM, so
it will not see Windows paths the same way your torrent client does.

## Install

Install [Node.js](https://nodejs.org/) 20 or newer, then install `cross-seed`:

```powershell
npm install -g cross-seed
cross-seed --version
```

Ignore `npm` deprecation warnings if `cross-seed --version` prints a version.
For example, a warning about `prebuild-install` does not mean installation
failed.

## Generate your config

```powershell
cross-seed gen-config
```

The default config directory is:

```text
C:\Users\<YourUsername>\AppData\Local\cross-seed
```

Edit the generated `config.js`. Restart `cross-seed` after every config change.

## Windows paths in `config.js`

Backslashes must be escaped in JavaScript strings. Use `\\` instead of `\`:

```js
module.exports = {
	torrentDir: "C:\\Users\\Me\\AppData\\Local\\qBittorrent\\BT_backup",
	dataDirs: ["D:\\Torrents\\Movies", "D:\\Torrents\\TV"],
	linkDirs: ["D:\\Torrents\\cross-seed"],
	torrentClients: ["qbittorrent:http://user:pass@localhost:8080"],
};
```

Do not mix Windows paths with Docker/Linux paths. If qBittorrent saves to
`D:\Torrents\Movies`, `cross-seed` also needs to run on Windows and see
`D:\Torrents\Movies`.

## Hardlink requirements

Hardlinks only work on filesystems that support them and only within the same
filesystem volume.

- NTFS supports hardlinks.
- exFAT does not support hardlinks.
- A hardlink from `C:` to `D:` will fail because those are different volumes.
- A hardlink from one network share to another is usually not supported.

To verify hardlinks in PowerShell, compare the link count or file ID:

```powershell
fsutil hardlink list "D:\Torrents\Movies\Movie.mkv"
fsutil file queryfileid "D:\Torrents\Movies\Movie.mkv"
fsutil file queryfileid "D:\Torrents\cross-seed\Tracker\Movie\Movie.mkv"
```

Hardlinked files share the same file ID on the same NTFS volume.

## Common Windows mistakes

- Running qBittorrent on Windows but `cross-seed` in Docker Desktop.
- Using `C:\Path\To\File` instead of `C:\\Path\\To\\File` in `config.js`.
- Putting `linkDirs` on a different drive than the source data.
- Using an exFAT drive for linked data.
- Editing a config file in the wrong user profile or config directory.

For Docker, Torznab, webhook, and permission checks, see
[Common Setup Failures](./common-setup-failures.md).
