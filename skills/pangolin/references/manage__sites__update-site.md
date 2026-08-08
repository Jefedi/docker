> ## Documentation Index
> Fetch the complete documentation index at: https://docs.pangolin.net/llms.txt
> Use this file to discover all available pages before exploring further.

# Update Sites

> Update Newt to the latest version

<div />

The update process depends on how you originally installed Newt.

Find the latest version in the [GitHub releases](https://github.com/fosrl/newt/releases).

## Docker Installation

Update the image version in your `docker-compose.yml`:

```yaml title="docker-compose.yml" theme={"theme":"gruvbox-light-hard"}
services:
  newt:
    image: fosrl/newt:{version} #  Replace {version} with the latest version tag
    # ... rest of config
```

Then pull and restart:

```bash theme={"theme":"gruvbox-light-hard"}
docker compose pull newt
docker compose up -d newt
```

## Binary Installation

### Auto Installer (Recommended)

If you used the auto installer, simply run it again.

```bash theme={"theme":"gruvbox-light-hard"}
curl -fsSL https://static.pangolin.net/get-newt.sh | bash
```

### Manual Installation

Download the latest binary for your system from [GitHub releases](https://github.com/fosrl/newt/releases) and replace your existing binary.

```bash theme={"theme":"gruvbox-light-hard"}
wget -O newt "https://github.com/fosrl/newt/releases/download/{version}/newt_{architecture}" && chmod +x ./newt
```

<Note>
  Replace `{version}` with the desired version and `{architecture}` with your architecture. Check the [release notes](https://github.com/fosrl/newt/releases) for the latest information.
</Note>
