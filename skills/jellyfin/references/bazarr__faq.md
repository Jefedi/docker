# FAQ

- [Where can I find the logs or database](#where-can-i-find-the-logs-or-database)
- [This path doesn't seems to be valid](#this-path-doesnt-seems-to-be-valid)
- [Why (or) do I need the Anti-Captcha](#why-or-do-i-need-the-anti-captcha)
- [Why doesn't Bazarr find any subtitles](#why-doesnt-bazarr-find-any-subtitles)
- [How do I enable the debug log](#how-do-i-enable-the-debug-log)
- [How to report a problem](#how-to-report-a-problem)
- [I'm a cloud user or run on a low powered device](#im-a-cloud-user-or-run-on-a-low-powered-device)
- [What are Forced Subtitles](#what-are-forced-subtitles)
- [What are Embedded Subtitles](#what-are-embedded-subtitles)
- [How do I reset my password](#how-do-i-reset-my-password)
- [Which external subtitles does Bazarr recognize](#which-external-subtitles-does-bazarr-recognize)
- [I'm missing or want a subtitle provider added to Bazarr](#im-missing-or-want-a-subtitle-provider-added-to-bazarr)
- [I would like to see the following Feature in Bazarr](#i-would-like-to-see-the-following-feature-in-bazarr)
- [Synchronization failed...](#synchronization-failed)

## Where can I find the logs or database

You can find the location for your database and log file in the following location depending where and how you installed it.

**Windows Installation:**
`%programdata%\Bazarr`

**Docker: linuxserver/bazarr**
`/config/db` and `/config/log`

**Docker: hotio/bazarr**
`/config/app/db` and `/config/app/log`

**Source and other Installation:**
`data directory inside bazarr root directory`

------

## This path doesn't seems to be valid

If you're getting a error that looks like this:

![image-20200723180256943](images/image-20200723180256943.png)

This can be for various reasons we've collected the the most common ones depending on the used OS.

### Windows

- **Bazarr service runs under Local System account that won't be able to access network shares.**
  Run Bazarr's service as another user that has access to that share.  You need to change the account used for Bazarr service in `services.msc` console.
- **You're using a mapped network drive (not a UNC path).**
  Change your paths to UNC paths (`\\server\share`) both in Sonarr, Radarr and Bazarr will be able to access those files.

### Docker

- **Your docker containers volume paths don't match with Sonarr/Radarr**
  make sure Bazarr uses the identical volume paths as Sonarr and Radarr.

### Docker & Synology when mixing packages with dockers

- In worse case scenario you need to make use of [Paths Mapping](https://github.com/morpheus65535/bazarr/wiki/Settings#path-mappings)

#### NOTE

> *If you're using docker and get this warning and need help with it provide us with the docker compose or docker build command of Bazarr and Sonarr/Radarr !!!*
>
> *If you're using a system with a GUI(Synology, unRAID, OMV, etc.) to configure docker use one of the following from terminal(puTTy) to get the docker compose or docker build command.*`
>
> `sudo docker run --rm -v /var/run/docker.sock:/var/run/docker.sock red5d/docker-autocompose CONTAINER_NAME`
>
> *And yes this even works on a Synology*
> *if you don't know how you probably didn't read the [[Installation-Synology]]*

------

## Why (or) do I need the Anti-Captcha

***Some providers require a Anti-Captcha when using their API.***

![image-20200723180451078](images/image-20200723180451078.png)

Choose the Anti-Captcha provider you want to use, and add the needed credentials.

We recommend [Anti-Captcha.com](https://anti-captcha.com/).

------

## Why doesn't Bazarr find any subtitles

Please check if you've configured the following settings.
[[First time installation configuration]]

------

## How do I enable the debug log

`Settings` => `General`
![enable debug log](images/image-20200519215100814.png)

------

## How to report a problem

1. Start with enabling the debug log.
2. Clear your logs and then try to replicate your issue.
3. Paste your logs on one of the following sites.
   - <https://gist.github.com/>
   - <https://hastebin.com/>
   - <https://pastebin.com/>
4. Follow the steps provided in [[Asking for help or report a problem]]

------

## I'm a cloud user or run on a low powered device

We've collected a few Tips & Tweaks that could help, you can find them in [[Performance-Tuning]]

------

## What are Forced Subtitles

Forced subtitles is the subtitle appearing on screen when the characters speak a foreign or alien language, or there is a sign, location, or other text in the scene.

- Like Dothraki in Game of Thrones.
- Star Trek when someone speaks Klingon.

------

## What are Embedded Subtitles

Embedded subtitles are subtitles that are in the video container (mkv, mp4, etc)
they can be different formats in the container ex. .srt, PGS, etc

------

## How do I reset my password

Edit your config.ini and change your auth type to None and restart Bazarr.

![image-20200725145930627](images/image-20200725145930627.png)

Your config.ini can be found in your [in the same location where your logs or database are](#where-can-i-find-the-logs-or-database)

------

## Which external subtitles does Bazarr recognize

Bazarr recognizes the following external subtitles during a disk scan to match which language subtitles you already got.

`.srt`, `.sub`, `.smi`, `.txt`, `.ssa`, `.ass`, `.mpl`, `.vtt`

------

## I'm missing or want a subtitle provider added to Bazarr

You're missing a subtitle provider or want one added to Bazarr ?
Well you got several ways to do that.

1. The fastest:

    Learn Python and create a provider script for Bazarr.
    You can can look in the source code which [providers](https://github.com/morpheus65535/bazarr/tree/master/libs/subliminal_patch/providers) we got and working on.
    If you need to write one then you can use the 2 following templates depending what the provider supports.
    - [API-Template](https://github.com/morpheus65535/bazarr/blob/master/libs/subliminal_patch/providers/napisy24.py)
    - [Page-Scrapping-Template](https://github.com/morpheus65535/bazarr/blob/master/libs/subliminal_patch/providers/soustitreseu.py)
    > If API is supported it is preferred.
    > Why ?
    > Easier Error management and Scrapping the site is more resource intensive.

2. The slowest:

    [Bazarr Feature Request](https://bazarr.featureupvote.com/)
    First check if no one else already requested it of no one requested it you can create a new Feature Request, make sure to use a clear topic and use a good description and why etc.

> **Keep in mind it doesn't mean it will happen, created or added !!!**
> **We highly discourage you from requesting providers in the Discord/Github.**
> **It will be ignored or forgotten !!!**

------

## I would like to see the following Feature in Bazarr

Go to [Bazarr Feature Request](https://bazarr.featureupvote.com/)

First check if no one else already requested it of no one requested it you can create a new Feature Request, make sure to use a clear topic and use a good description and why etc.

>***Keep in mind it doesn't mean it will happen, created or added !!!***

------

## Synchronization failed...

If you have left over `*.synced.*` files or if you get the following error or similar:

`Synchronization failed; consider passing --max-offset-seconds with a number larger than 600`

This Should be reported to [smacke ffsubsync Github](https://github.com/smacke/ffsubsync) by providing the subtitles synchronization debug log that is created by enabling `Subtitles synchronization debugging` in Settings-->Subtitles.

This isn't a issue we can fix or do anything about it ourselves, So no need to report to us

------
