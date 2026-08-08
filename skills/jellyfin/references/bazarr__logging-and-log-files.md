If you need help with Bazarr or want to report a problem it's best to start with a Debug log.

### How do you enable the debug log

`Settings` => `General`

![](images/image-20200519215100814.png)

### Where can you find the logs

You can find the location for your database and log file in the following location depending where and how you installed it.

**Windows Installation:** `%programdata%\Bazarr`

**Dockers: linuxserver/bazarr** `/config/db` and `/config/log`

**Dockers: hotio/bazarr** `/config/app/db` and `/config/app/log`

**Source and other Installation:** `data directory inside bazarr root directory`

### How and where do you provide the logs

1. Clear your logs and then try again to replicate your issue.
2. Paste your logs on one of the following site.

- <https://gist.github.com/>
- <https://hastebin.com/>
- <https://pastebin.com/>

3. Follow the step provided in [[Asking for help or report a problem]]
