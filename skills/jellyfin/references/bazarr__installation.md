- [Windows](#windows)
- [Docker](#docker)
- [Linux](#linux)
- [MacOS](#macos)
- [FreeBSD](#freebsd)
- [Synology](#synology)

### Windows

To install Bazarr on Windows 7 or greater, just use our automated installer: [Bazarr installer](https://github.com/bazarr/bazarr.github.io/releases/latest/download/bazarr.zip)

> **Please keep in mind that, by default, the Bazarr service will run under Local System account that won't be able to access network shares. You need to change the account used for Bazarr service in `services.msc` console.**

If you install Bazarr in the `Program Files` directory, the account under which it runs **must have administrative privileges** for Bazarr to be able to update itself.

Bazarr settings, logs and db are stored in `C:\ProgramData\Bazarr`. Keep in mind you'll need to change permission on this directory if you change Bazarr service account to something else than System.

The start menu shortcut (it opens the web UI) won't work anymore if you change Bazarr listening port or IP address.

Bazarr installed through this installer won't update from any other branch other than master. If you've hard coded something else in `config.ini`, you must change it back to `master`.

**or you can run it from source the following way:**

bazarr requires Python 3.7 or greater and can be run from source.

1. Install Python 3.7 or greater (Till [Python 3.8.6](https://www.python.org/downloads/release/python-386/) Tested) from [this link](https://www.python.org/downloads/release/python-386/) and make sure to check the box to have Python directory added to the system path variable.
2. Open up CMD and go to the folder you want to install bazarr. Do not use `C:\Program Files` or `C:\Program Files (x86)` as you could run into strange issues. Something like `C:\bazarr` is a better choice.
3. Download latest release of Bazarr [here](https://github.com/morpheus65535/bazarr/archive/refs/heads/master.zip)
4. Extract the content of the zipped release to the previously created `bazarr` directory
5. Go to the bazarr folder `cd bazarr`
6. Install Python requirements using `pip install -r requirements.txt`
7. You can now start bazarr via `python bazarr.py` to start bazarr.
8. Open your browser and go to `http://localhost:6767/`

------

------
### Docker

> **You CANNOT store your config directory over an NFS share as it is unsupported by SQLITE. You'll face a locked database error.**

Feel free to use any of the following well maintained images, in no particular order:

### [hotio/bazarr](https://hub.docker.com/r/hotio/bazarr)

Maintained by: [hotio](https://github.com/hotio)  
Available tags: `latest` (=`stable`), `nightly`  
Versioned tags: `stable-0.8.3.4`, `nightly-8d9023af80974ff09fef3fb8b5f2c51a4923de1f`  
Updates: `every 30 minutes for apps and every hour for upstream image updates`

Configuration files for Bazarr are stored in `/config/app`. 

### [linuxserver/bazarr](https://hub.docker.com/r/linuxserver/bazarr)

Maintained by: [linuxserver](https://github.com/linuxserver)  
Available tags: `latest` and `development`  
Versioned tags: `v0.8.3.4-ls59` and `600ef3ab-ls62`  
Updates: `regular and timely application updates`

Configuration files for Bazarr are stored in `/config`.

> For more info on how to configure the images, info about their used tags and their correlation to bazarr branches, visit their respective Docker Hub pages.

------

------

### Linux

- (Ubuntu / Debian) Install requirements with `apt-get install python3-pip python3-distutils`

- (Fedora / CentOS) Install requirements with `yum install python3-pip python3-distutils`

- (Raspbian and maybe other ARM based distro) - (*thnx to @inquilino for the fixes/updates*)

  > `sudo apt-get update`
  > `sudo apt-get install libxml2-dev libxslt1-dev python3-libxml2 python3-lxml unrar-free ffmpeg libatlas-base-dev`

1. Upgrade Python to version 3.7 or greater.
2. Download latest release of Bazarr [here](https://github.com/morpheus65535/bazarr/archive/refs/heads/master.zip)
3. Extract the content of the zipped release to the previously created `bazarr` directory
4. Install Python requirements using `python3 -m pip install -r requirements.txt`

   > (Raspbian) Don't worry about `lxml` not being installed at this step, you have installed the module through `apt-get` anyway.
5. Change ownership to your preferred user for running programs (replace both instances of $user)
   
   `sudo chown -R $user:$user /opt/bazarr`
5. You can now start bazarr via `python3 bazarr.py` to start bazarr.
6. Open your browser and go to `http://localhost:6767/`

------

------
### MacOS

bazarr requires Python 3.7.x or 3.8.x (**system Python 2.7.10 not supported**) and can be run from source.

1. Install Python from [this link](https://www.python.org/ftp/python/3.8.6/python-3.8.6-macosx10.9.pkg)
2. Open Terminal
3. Change Directory To Applications `cd /Applications` and create a `bazarr` directory
4. Download latest release of Bazarr [here](https://github.com/morpheus65535/bazarr/archive/refs/heads/master.zip)
5. Extract the content of the zipped release to the previously created `bazarr` directory
6. Change Directory To bazarr `cd bazarr`
7. Install bazarr requirements `python3.8 -m pip install -r requirements.txt`
8. Run bazarr `python3.8 bazarr.py`

bazarr will run in this Terminal session. Closing the session will stop bazarr. You can start it up again using 3, 4, 6, 7 and 8.

Access bazarr via browser at https://localhost:6767/

------

------
### FreeBSD

Instruction as provided by @Derkades and fixes by @sindreruud

Disclaimer: I don't know how rc.d works so the script is pretty crappy and doesn't have start/stop/status functionality. It only starts the program on startup, which was enough for me.

1. Install the required software `pkg update && pkg install python3 py3X-pip py3X-libxml2 libxslt py3X-sqlite3 unrar ffprobe` where `py3X` must be replaced with the Python3 version you use for Bazarr.
2. `cd /usr/local/share`
3. Create a `bazarr` directory
4. Download latest release of Bazarr [here](https://github.com/morpheus65535/bazarr/archive/refs/heads/master.zip)
5. Extract the content of the zipped release to the previously created bazarr directory
6. `cd bazarr`
7. Install Python requirements using `python3 -m pip install -r requirements.txt`
8. Check if it works `python3 bazarr.py`. You should see `BAZARR is started and waiting for request on http://0.0.0.0:6767/`

------

------
### Synology

See: [[Installation Synology]]