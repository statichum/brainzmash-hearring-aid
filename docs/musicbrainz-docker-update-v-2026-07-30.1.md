# MusicBrainz Docker Update to v-2026-07-30.1

Run these commands on each MusicBrainz backend server.

## 1. Open the MusicBrainz Docker directory

```bash
cd /docker/musicbrainz-docker
```

Use the server's actual MusicBrainz Docker path if it differs.

## 2. Discard the old tracked modifications

```bash
git reset --hard HEAD
```

Do not run `git clean`. The command above does not remove untracked files or Docker volumes.

## 3. Update to v-2026-07-30.1

```bash
git fetch --tags origin
git checkout v-2026-07-30.1
```

## 4. Build and start the updated containers

```bash
docker compose up --build -d
```

## 5. Restore hourly replication

```bash
nano default/replication.cron
```

Set the file contents to:

```cron
SHELL=/bin/bash
BASH_ENV=/noninteractive.bash_env
5 * * * * cd /musicbrainz-server && /usr/local/bin/replication.sh >> /musicbrainz-server/mirror.log 2>&1
```

## 6. Reload the replication cron configuration

```bash
docker compose down
docker compose up -d
```

## 7. Verify the update and schedule

```bash
git describe --tags --always --dirty
docker compose ps
docker compose exec musicbrainz crontab -l
```

Expected version:

```text
v-2026-07-30.1-dirty
```

The `-dirty` suffix is expected because `default/replication.cron` was modified.

The replication workaround and previous index-setting changes are intentionally not reapplied. Allow the unmodified July release to run replication first.
