- [Windows](#windows)

- [Linux](#linux)

- [MacOS](#macos)

- [FreeBSD](#freebsd)

  

### Windows

> If you used the installer then it's already set to autostart.**
If you installed it in another way in windows you can use the following.

#### Installing Bazarr as a Windows Service using NSSM

1. Download the latest NSSM from <https://nssm.cc/download>. It is recommended to grab the prerelease due to a slight issue with the Windows 10 Creators Update.

2. Either place the downloaded NSSM binary in `C:\Windows\System32`, or add it to your `PATH`. This is to allow you to use NSSM from any location.

3. Run `cmd` as an Administrator and use the command `nssm install bazarr`

4. A GUI should pop up. Use the following configuration

- Path: Should be the location to your Python 3.8 executable. Example: `C:\Python38\python.exe`

- Startup Directory: Should be the location of your `Python38` folder. Example: `C:\Python38`

- Arguments: Should be the location of your `bazarr.py` file. Example: `C:\bazarr\bazarr.py`

> Please note that running Bazarr from the `Program Files` or `Program Files (x86)` directories may cause issues.

5. Under `Process Tab`, make sure to uncheck `Console Windows`.

6. Click the `Install Service` button

7. Use the command `nssm start bazarr` to initiate bazarr. It should autostart going forward.

`nssm edit bazarr` will open up the GUI for further edits.
`nssm restart bazarr` will restart bazarr.
`nssm stop bazarr` will stop bazarr.
`nssm remove bazarr` will remove the Windows Service.

- Note that this guide will work in essence for any Python script, and you can use NSSM to run most things as Windows Services through some tweaking of this overall config.

------

### Linux

In any case, the user must have a home directory!!!

#### systemd service file for Debian Ubuntu

> **Be aware that this is provided as-is without any support from the team.**

This is a systemd service file created by users of Bazarr. It assumes you've installed Bazarr in: `/opt/bazarr`.

You have to create a `bazarr.service` file in `/etc/systemd/system` that would contain the following text:

```php
[Unit]
Description=Bazarr Daemon
After=syslog.target network.target

# After=syslog.target network.target sonarr.service radarr.service

[Service]
WorkingDirectory=/opt/bazarr/
User=your_user(username of your choice)
Group=your_group(group of your choice)
UMask=0002
Restart=on-failure
RestartSec=5
Type=simple
ExecStart=/usr/bin/python3 /opt/bazarr/bazarr.py
KillSignal=SIGINT
TimeoutStopSec=20
SyslogIdentifier=bazarr
ExecStartPre=/bin/sleep 30

[Install]
WantedBy=multi-user.target
```

Start the service using `sudo systemctl start bazarr`

Check if the service is running using `sudo systemctl status bazarr`

If it's running without errors then you need to enable the service using `sudo systemctl enable bazarr`



#### Upstart script for Debian Ubuntu

This is an init upstart file. It assumes you've installed Bazarr in: `/opt/bazarr`

You have to create a `bazarr.conf` file in `/etc/init/` (`sudo nano /etc/init/bazarr.conf`) that would contain the following text:

```php
description "Upstart Script to run Bazarr as a service on Ubuntu/Debian based systems, as well as others"
author "A Bazarr User"

#Set user and group for the process if desired
#setuid myUserID
#setgid myGroupID

#start after all services come up
start on runlevel [2345]
stop on runlevel [016]

# Automatically restart process if crashed

respawn

# Make sure script is started with system locale

script
   if [ -r /etc/default/locale ]; then
       . /etc/default/locale
       export LANG
   fi
   exec python /opt/bazarr/bazarr.py
end script
```

------

### MacOS

#### LaunchAgent on MacOS

As-is, the LaunchAgent expects bazarr to be cloned or installed at `/Applications/bazarr`. If this is counter to other documentation I recommend amending the file contents.

The LaunchAgent should be named `com.github.morpheus65535.bazarr.plist` -  again, if you'd like something else, update the Label in the file itself as well.

The file is installed to `/Library/LaunchAgents` and the service will start when the user logs into the system. After installation, the service can be started immediately by running `launchctl load /Library/LaunchAgents/com.github.morpheus65535.bazarr.plist`. The service can be stopped by running the same command replacing load with unload.

Make sure that owner and permissions are properly defined on the plist:
```
sudo chown root:wheel /Library/LaunchAgents/com.github.morpheus65535.bazarr.plist
sudo chmod -R 0644 /Library/LaunchAgents/com.github.morpheus65535.bazarr.plist
```

Logs are written to `/usr/local/var/log/bazarr.log`.

Here's the file:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.github.morpheus65535.bazarr</string>
    <key>ProgramArguments</key>
    <array>
      <string>/usr/local/bin/python3.8</string>
      <string>/Applications/bazarr/bazarr.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/usr/local/var/log/bazarr.log</string>
    <key>StandardOutPath</key>
    <string>/usr/local/var/log/bazarr.log</string>
  </dict>
</plist>
```

------

### FreeBSD

#### Starting on boot

- A user needs to be created for Bazarr to run as a daemon, the script is written for a user called bazarr but this can be changed by modifying `bazarr_user="bazarr"` in `/etc/rc.conf`
- Change permissions on Bazarr directory by running the following command: `chown -R bazarr_user /usr/local/share/bazarr` where bazarr_user is the user you've created.
- `nano /usr/local/etc/rc.d/bazarr`
- Enter this:

```bash
#!/bin/sh
# PROVIDE: bazarr
# REQUIRE: LOGIN
# KEYWORD: shutdown

# Add the following lines to /etc/rc.conf to enable bazarr:
# bazarr_enable="YES"
# Optionally add:
# Note: The bazarr_user must be unique as the stop_postcmd kills the other running process
# bazarr_user="bazarr"

. /etc/rc.subr

name="bazarr"
rcvar=bazarr_enable

load_rc_config $name

: ${bazarr_enable="NO"}
: ${bazarr_user:="bazarr"}
: ${bazarr_data_dir:="/usr/local/bazarr"}

pidfile="/usr/local/share/bazarr/bazarr.pid"
procname="/usr/local/bin/python3"
command="/usr/sbin/daemon"
command_args="-f -p ${pidfile} ${procname} /usr/local/share/bazarr/bazarr.py"

start_precmd=bazarr_precmd
stop_postcmd=bazarr_postcmd

bazarr_precmd()
{
	export XDG_CONFIG_HOME=${bazarr_data_dir}
        export GIT_PYTHON_REFRESH=quiet

	if [ ! -d ${bazarr_data_dir} ]; then
		install -d -o ${bazarr_user} ${bazarr_data_dir}
	fi
}

bazarr_postcmd()
{
	killall -u ${bazarr_user}
}

run_rc_command "$1"
```

- Save and exit (ctrl+x - y - enter)
- Make the file executable `chmod +x /usr/local/etc/rc.d/bazarr`
- `nano /etc/rc.conf`
- On the last line, add bazarr_enable="YES"
- Reboot
