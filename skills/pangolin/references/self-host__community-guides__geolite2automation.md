> ## Documentation Index
> Fetch the complete documentation index at: https://docs.pangolin.net/llms.txt
> Use this file to discover all available pages before exploring further.

# GeoLite2 Automation

> A simple automation to download & update your GeoLite2 databases with geoipupdate

<div />

<Note>
  This is a community guide and is not officially supported. If you have any issues, please reach out to the [author](https://github.com/txwgnd).
</Note>

This automation lets your system automatically download and update the `GeoLite2-Country` and `GeoLite2-ASN` databases from MaxMind. Pangolin uses these databases for geo-location features such as country or region rules, geo-blocking, analytics, and ASN blocking. It uses MaxMind's [geoipupdate](https://github.com/maxmind/geoipupdate/tree/main) Docker container to do this.

Maxmind's service is free of charge for development, personal or community use. [Quote](https://support.maxmind.com/knowledge-base/articles/create-a-maxmind-account#h_01G4G4NG5C63BQ6HRG6MSS50T3)

# Table of Contents

1. **[Requirements](#1-requirements)**
2. **[Maxmind Account](#2-maxmind-account)**
3. **[API key creation](#3-api-key-creation)**
4. **[Modification of Pangolin's `docker-compose.yml`](#4-modification-of-pangolins-docker-compose-yml)**
5. **[Modification of Pangolin's `config.yml`](#5-modification-of-pangolins-config-yml)**

## 1. Requirements

* A Maxmind account for API access
* Pangolin version 1.11.0 or higher

## 2. Maxmind Account

To be able to use Maxmind's service you need to request access to the GeoLite2 databases and create an account on their [website](https://www.maxmind.com/en/geolite2/signup?utm_source=kb\&utm_medium=kb-link\&utm_campaign=kb-create-account).

After you successfully created an account visit the mainpage again and login to your new account.

## 3. API key creation

The next step is to create an API key for `geoipupdate`. You'll find an entry called `Manage license keys` in the menu on the left side. Head to this page and click on `Generate new license key`.

<Frame caption="Maxmind's Manage license keys page">
  <img src="https://mintcdn.com/fossorial/WZ4OcypdChdYMxya/images/maxmind_manage-license-keys.jpeg?fit=max&auto=format&n=WZ4OcypdChdYMxya&q=85&s=45cc57507e2f28814baceabeac81da9a" alt="Maxmind's Manage license keys page" width="2792" height="1634" data-path="images/maxmind_manage-license-keys.jpeg" />
</Frame>

Give your new key a name. E.g. `Pangolin`.

<Frame caption="Choose a name for the key">
  <img src="https://mintcdn.com/fossorial/WZ4OcypdChdYMxya/images/maxmind_create-key-page.jpeg?fit=max&auto=format&n=WZ4OcypdChdYMxya&q=85&s=0558ff4f3da32cc7622bb516b736e72a" alt="Maxmind's key creation page" width="2014" height="624" data-path="images/maxmind_create-key-page.jpeg" />
</Frame>

After your key got created the webpage will show you your Account ID as well as the API key. Save the key now because it can only be seen once. Don't panic if something goes wrong, you can easily create new keys.

<Frame caption="Key successfully created">
  <img src="https://mintcdn.com/fossorial/WZ4OcypdChdYMxya/images/maxmind_key-created.jpeg?fit=max&auto=format&n=WZ4OcypdChdYMxya&q=85&s=538be94f872890457482ecb8ec9289f1" alt="The key got created successfully" width="1960" height="570" data-path="images/maxmind_key-created.jpeg" />
</Frame>

After you clicked on `Return to list` you should see an overview of your keys bundled with some metadata.

## 4. Modification of Pangolin's `docker-compose.yml`

Now login to your Pangolin host and navigate to `/pangolin` in your user directory:

```bash theme={"theme":"gruvbox-light-hard"}
cd pangolin
```

Shut down Pangolin with:

```bash theme={"theme":"gruvbox-light-hard"}
docker compose down
```

Open `docker-compose.yml` with your favorite text editor.
E.g. nano:

```bash theme={"theme":"gruvbox-light-hard"}
nano docker-compose.yml
```

Append this Docker compose service at the end of your stack and add your Account ID as well as your API key you created in the last step:

```yaml theme={"theme":"gruvbox-light-hard"}
services:
  (...)
  geoipupdate:
    container_name: geoipupdate
    image: ghcr.io/maxmind/geoipupdate
    restart: unless-stopped
    environment:
      - 'GEOIPUPDATE_ACCOUNT_ID='							# Account ID
      - 'GEOIPUPDATE_LICENSE_KEY='							# API key
      - 'GEOIPUPDATE_EDITION_IDS=GeoLite2-Country GeoLite2-ASN'	# Which dbs should be downloaded
      - 'GEOIPUPDATE_FREQUENCY=72'							# Update intervall in hours
    volumes:
      - './config/GeoLite2:/usr/share/GeoIP'
```

#### Note

If you use the standard Pangolin deployment you shouldn't need to modify the path.
This is the bare minimum to run the container. There are other optional environment variables available. Have a look at their [docs](https://dev.maxmind.com/geoip/updating-databases/?lang=en)!

Save and close the file, but don't restart the stack yet!

## 5. Modification of Pangolin's config.yml

Navigate to `/config` within the same folder and open it with a text editor.

```bash theme={"theme":"gruvbox-light-hard"}
cd config
```

Add these lines to the `server` object

```yaml theme={"theme":"gruvbox-light-hard"}
server:
  maxmind_db_path: "./config/GeoLite2/GeoLite2-Country.mmdb"
  maxmind_asn_path: "./config/GeoLite2/GeoLite2-ASN.mmdb"
```

These entries tell the Pangolin application where to find the databases.

Save and close the file then navigate to the `pangolin` folder one level higher.

Restart your Pangolin stack with:

```bash theme={"theme":"gruvbox-light-hard"}
docker compose up -d
```

Et voilà, you are now able to define country rules and ASN rules for your resources! 🏁

btw: you can use these exact databases for your Traefik dashboard too -> [Community Guide](/self-host/community-guides/traefiklogsdashboard)
