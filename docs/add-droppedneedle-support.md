# Add Dropped Needle support to an existing BrainzMash backend

This adds the read-only MusicBrainz endpoints used by Dropped Needle to an
existing BrainzMash LMD proxy.

These instructions assume that the existing BrainzMash setup is working and
that the `artist` and `release` search indexes have already been built.

## 1. Add the MusicBrainz dependency

Open:

```bash
nano ./local/compose/brainzmash-nginx.yml
```

Add `musicbrainz` beneath the existing `lmd` dependency:

```yaml
    depends_on:
      - lmd
      - musicbrainz
```

Save the file.

## 2. Replace the Nginx configuration

First, make a note of the existing private BrainzMash key:

```bash
grep 'set $expected_key' ./local/compose/brainzmash/nginx.conf
```

Keep that key private. You will insert the same key into the replacement
configuration below.

Open the configuration:

```bash
nano ./local/compose/brainzmash/nginx.conf
```

Replace its contents with the following, then replace
`YOUR_EXISTING_BRAINZMASH_KEY` with the key you noted above:

```nginx
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    server {
        listen 80;

        set $expected_key "YOUR_EXISTING_BRAINZMASH_KEY";

        # Authenticate every request, including LMD and MusicBrainz.
        if ($http_x_brainzmash_key != $expected_key) {
            return 403;
        }

        # Read-only MusicBrainz endpoints required by Dropped Needle.
        location ~ ^/ws/2/(artist|release-group|release|recording|isrc|url)(?:/[^/]+)?/?$ {
            limit_except GET {
                deny all;
            }

            proxy_pass http://musicbrainz:5000;
            proxy_http_version 1.1;

            proxy_set_header Host $host;
            proxy_set_header Connection "";
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            proxy_connect_timeout 5s;
            proxy_read_timeout 30s;
        }

        # Reject every other MusicBrainz API endpoint.
        location /ws/2/ {
            return 404;
        }

        location = /ws/2 {
            return 404;
        }

        # Existing LMD endpoint.
        location / {
            proxy_pass http://lmd:5001;
            proxy_http_version 1.1;

            proxy_set_header Host $host;
            proxy_set_header Connection "";
        }
    }
}
```

Save the file.

## 3. Recreate the proxy

```bash
docker compose up -d --force-recreate musicbrainz-docker-brainzmash-nginx
```

Check the Nginx configuration:

```bash
docker compose exec musicbrainz-docker-brainzmash-nginx nginx -t
```

## 4. Build the additional search indexes

The normal BrainzMash setup already builds the `artist` and `release` indexes.
Dropped Needle also requires `release-group` and `recording`:

```bash
docker compose exec indexer python -m sir reindex \
  --entity-type release-group \
  --entity-type recording
```

This can take several hours. Wait for both imports to finish and for the command
to return to the shell prompt before testing.

## 5. Test the new endpoints

From within the `musicbrainz-docker` directory, load the existing BrainzMash
key from the Nginx configuration:

```bash
BM_KEY=$(
  sed -n 's/.*set $expected_key "\([^"]*\)";.*/\1/p' \
    ./local/compose/brainzmash/nginx.conf
)
```

Test release-group search:

```bash
curl -fsS -G \
  -A 'DroppedNeedleApp/backend-test' \
  -H "X-BrainzMash-Key: $BM_KEY" \
  --data-urlencode 'query=(releasegroup:"OK Computer" OR release:"OK Computer") AND artist:"Radiohead"' \
  --data 'limit=10' \
  --data 'fmt=json' \
  'http://127.0.0.1:5002/ws/2/release-group' \
  | jq -e '."release-groups" | any(.id == "b1392450-e666-3926-a536-22c65f834433")'
```

Test recording search:

```bash
curl -fsS -G \
  -A 'DroppedNeedleApp/backend-test' \
  -H "X-BrainzMash-Key: $BM_KEY" \
  --data-urlencode 'query=recording:"Airbag" AND artist:"Radiohead"' \
  --data 'limit=10' \
  --data 'fmt=json' \
  'http://127.0.0.1:5002/ws/2/recording' \
  | jq -e --arg artist 'a74b1b7f-71a5-4011-9441-d0b5e4122711' \
      '.recordings | any(.title == "Airbag" and any(."artist-credit"[]?; .artist.id == $artist))'
```

Each command should print:

```text
true
```

## 6. Request the external check

Ask Statichum on Discord to check that your instance is passing the Dropped
Needle response checks.
