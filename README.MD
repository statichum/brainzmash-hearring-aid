# MusicBrainz Mirror with Lidarr Metadata Server Setup Guide

Original project by [blampe](https://github.com/blampe/hearring-aid)
This fork contains fixes for image and wiki sourcing.


This guide will help you deploy a local MusicBrainz mirror, and integrate it with Lidarr using the Tubifarry plugin. It walks through host and container setup, basic configuration, and validation steps to ensure the system is working properly.

You no longer need the plugins branch of lidarr in order to install Tubifarry and set a custom metadata server, currently plugins are avaiaible in lscr.io/linuxserver/lidarr:nightly

In setting this up, please consider becoming a part of the BrainzMash community loadbalanced Lidarr API Metadata server pool (shit that's a mouthful huh?) https://www.reddit.com/r/Lidarr/comments/1qkb15s/brainzmash_lidarr_community_metadata_network/


> **Note:**  
> This guide is based on Debian 12 and Docker. It is provided as-is and without warranty, and your feedback and testing results are appreciated!

---

## Prerequisites

- At least 8GB RAM, a moderately capable CPU, and 100GB of free disk space
- Best to run the database on a SSD volume rather than spinning disks
- Basic familiarity with Docker and command line
- Internet connection
- Docker Compose

## Notes before you start

- Adjust IP addresses and volume paths to match your environment.
- Initial DB creation, indexing, and replication can take several hours; be patient!
- Replace all placeholder keys (Spotify, Fanart.tv, Last.fm, etc.) with your own API keys.


---

## 1. Generate MusicBrainz Replication Token

1. Visit https://metabrainz.org/supporters/account-type and select your account type (usually "Non-commercial").
2. Go to https://metabrainz.org/profile and create an access token.
3. Save the 40-character alphanumeric token for later.

---

## 2. Setup MusicBrainz Docker Environment

```bash
mkdir -p /opt/docker && cd /opt/docker
git clone https://github.com/metabrainz/musicbrainz-docker.git
cd musicbrainz-docker
```

### 2.1 Download and run BrainzMash Bootstrap script

- Download the script
```
curl -fsSL -o brainzmash-bootstrap.sh https://raw.githubusercontent.com/statichum/brainzmash-bootstrap/main/brainzmash-bootstrap.sh
```
- Run the script
```
bash brainzmash-bootstrap.sh
```
- Remove the script (only needed once)
```
rm brainzmash-bootstrap.sh
```

### 2.2 Configure Lidarr Metadata Server

edit `local/compose/lmd-settings.yml` to add your keys:

```
nano local/compose/lmd-settings.yml
```

- Replace all placeholder keys (Spotify, Fanart.tv, Last.fm, etc.) with your own API keys.

---

### 2.3 Share API Key with Brainzmash operator

- 👋🏼 https://discord.gg/MSTteNvANt

---

## 4. Build and Initialize MusicBrainz Database

```bash
docker compose build
docker compose run --rm musicbrainz createdb.sh -fetch   # This may take an hour or more
docker compose up -d
docker compose exec indexer python -m sir reindex --entity-type artist --entity-type release  # Indexing may take a couple hours
```

---

## 5. Schedule Weekly Index Updates

Edit `/etc/crontab` and add:

```
0 1 * * 7 root cd /opt/docker/musicbrainz-docker && /usr/bin/docker compose exec -T indexer python -m sir reindex --entity-type artist --entity-type release
```

---

## 6. Configure Replication Token and Start Replication

```bash
docker compose down
admin/set-replication-token   # Enter your replication token when prompted
admin/configure add replication-token
docker compose up -d
docker compose exec musicbrainz replication.sh   # Run initial replication; use screen to keep it running
admin/configure add replication-cron
docker compose down   # Wait for replication to finish before restarting
rm -rf volumes/dbdump/*   # Clean up, saves ~6GB
docker compose up -d
```

---

## 6.1 (Optional Recommendation) Customise Replication Frequency and Set Up Logging

- Edit replication cron file
```default/replication.cron
```

- Recommended: Run 3hrly replications and set logs
```
0 */3 * * * cd /musicbrainz-server && /usr/local/bin/replication.sh >> /musicbrainz-server/mirror.log 2>&1
```

- Later, if need-be you can check the replicatin logs for troubleshooting by running:
```
docker exec -it musicbrainz-docker-musicbrainz-1 \
tail -f /musicbrainz-server/mirror.log
```
-Restart the container after these changes
---

## 7. Initialize Lidarr Metadata Server Database

```bash
docker exec -it musicbrainz-docker-musicbrainz-1 /bin/bash
cd /tmp
git clone https://github.com/Lidarr/LidarrAPI.Metadata.git
psql postgres://abc:abc@db/musicbrainz_db -c 'CREATE DATABASE lm_cache_db;'
psql postgres://abc:abc@db/musicbrainz_db -f LidarrAPI.Metadata/lidarrmetadata/sql/CreateIndices.sql
exit
docker compose restart
```

---

## 8. Using the Lidarr Metadata Server

- Your Lidarr metadata server is available at: `http://host-ip:5001`

---

## 9. Ensure you're running a branch of Lidarr that's plugins-capable

- At present that's the nightly image

```
lscr.io/linuxserver/lidarr:nightly
```

---

## 9.1 Configure Tubifarry Plugin in Lidarr

1. Open your browser to `http://host_ip:8686` and complete initial setup.
2. Navigate to **System > Plugins**.
3. Install **Tubifarry plugin** by entering the URL:  
   `https://github.com/TypNull/Tubifarry`  
   and click **Install**.
4. Restart Lidarr and after Lidarr restarts, log back into Lidarr and go to **Settings > Metadata**.
5. Under **Metadata Consumers**, select **Lidarr Custom**.
6. Check both boxes and enter your metadata server URL (e.g., `http://host_ip:5001`) in the **Metadata Source** field.
7. Save changes and restart Lidarr again:  
    ```bash
    docker compose restart
    ```

---

## 10. Verify and Troubleshoot

Follow these steps to test the setup and resolve common issues.

### ✅ Basic Functionality Test

- Open Lidarr and search for a new artist.  
  - If metadata loads correctly, your setup is working.
  - If you receive an error in Lidarr, proceed below.

### 🌐 Test Metadata Server (`lmd`) in Browser

To confirm that `lmd` is serving metadata properly, visit this URL in your browser (replace `host_ip` with your Docker host’s IP):

```
http://host_ip:5001/artist/1921c28c-ec61-4725-8e35-38dd656f7923
```

You should see a JSON response with artist details for **I Prevail**. If not:

- Validate that MusicBrainz is running:

  ```bash
  docker ps --filter "name=musicbrainz-docker-lmd-1"
  ```

  - If not running, perform a **clean restart** of the stack.

- If the container is running, check the logs for errors:

  ```bash
  docker logs -f musicbrainz-docker-lmd-1
  ```

  - Look for any errors or failed service messages that might indicate why data isn't being returned. A clean restart will likely resolve errors in the `lmd` container such as:

  ```text
  asyncpg.exceptions.UndefinedTableError: relation "wikipedia" does not exist
  ```
  > (`wikipedia`, `fanart`, `tadb`, or other missing tables)

### 🌐 Test MusicBrainz instance (`musicbrainz`)

To confirm your MusicBrainz mirror is functioning, visit this URL in your browser (replace `host_ip` with your Docker host’s IP):

```
http://host_ip:5000/artist/1921c28c-ec61-4725-8e35-38dd656f7923
```

You should see the artist page for **I Prevail**. If not:

- Validate that MusicBrainz is running:

  ```bash
  docker ps --filter "name=musicbrainz-docker-musicbrainz-1"
  ```

  - If not running, perform a **clean restart** of the stack.

- If the container is running, check the logs for errors:

  ```bash
  docker logs -f musicbrainz-docker-musicbrainz-1
  ```

### 🔁 Clean Restart of the Stack

It's super quick and easy to perform a clean restart, so please try this before asking for support or opening an issue:

```bash
cd /opt/docker/musicbrainz-docker
docker compose down -v && sleep 60 && docker compose up -d
```

> Wait a minute or two after restarting to allow all services to fully initialize.


---

## 11. Become Part Of the BrainzMash Server Pool

-The BrainzMash server pool is a load balanced community group of Lidarr Metadata servers just like the one you just put together. We pool our resources to provide this working metadata for Lidarr users frustrated with the official metadata and its 'quirks'.

- Your server stays private, you share the address with me privately, I add it to the pool, that's it. You'll only recieve traffic from my frontdoor server, not direct from end users.
- Load balancing is a simple round-robbin, if needed I can add weighting to increase or reduce load on your server as needed
- Opt in or out at any time of course
- The froontdoor server caches responses to significantly reduce load on backend servers like yours
- It forms a quorum from multiple mirrors and rejects any server that doesn’t match the majority data fingerprint to ensure we're serving quality data
- Replication status of each server is checked every 6 hours to make sure it's within 24h, if outside, your server will be rejected until next check. I run replication every 3h on both of my metadata servers, if you can do the same, that'd be ideal.
- A janky dashboard for server stats is here: https://dash.brainzmash.cc/

---




# For those updating to this image from blampe's original image

>If you're updating from blampe's blampe/lidarr.metadata:70a9707 image, follow the instructions below

## 1. cd to your musicbrainz docker folder, wherever that is for you:

```cd /opt/docker/musicbrainz-docker```


## 2. Stop docker container

```
docker compose down
```

## 3. Change image name for lmd-settings.yml

```
nano ./local/compose/lmd-settings.yml
```

- Change image name to 
```
statichum/brainzmash-hearring-aid:latest
```

## 4. Restart the container stack

```
docker compose up -d
```

## 5. LMD stores image url’s for 30 days and wiki for 7, it may store invalid links from the old setup so we’ll clear all LMD caches:

- Enter the db contianer and clear LMD cache
> This only clears LMD cache tables — it does NOT affect your MusicBrainz database.
```
docker exec -it musicbrainz-docker-db-1 sh
```

```
psql -U abc -d lm_cache_db -c "TRUNCATE artist, tadb, fanart, album, spotify, wikipedia;"
```

```
exit
```

Done! Test it.

---
