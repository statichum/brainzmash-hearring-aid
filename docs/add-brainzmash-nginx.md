# Add Brainzmash Nginx proxy

## 1. Create brainzmash-nginx.yml

- From within your Musicbrainz docker folder

```
nano ./local/compose/brainzmash-nginx.yml
```

- paste

```
services:
  musicbrainz-docker-brainzmash-nginx:
    container_name: musicbrainz-docker-brainzmash-nginx
    image: nginx:stable
    ports:
      - "5002:80"
    volumes:
      - ./local/compose/brainzmash/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - lmd
      - musicbrainz
    restart: unless-stopped

``` 

- save

## 2. Create NGINX config

- Make directory

```
mkdir -p ./local/compose/brainzmash
```
- Add config

```
nano ./local/compose/brainzmash/nginx.conf
```

- Paste

```
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    server {
        listen 80;

        # Inserted by setup script
        set $expected_key "__BRAINZMASH_KEY__";

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

- Save

## 2.1 Generate and insert API key

- Generate and insert key

```
KEY=$(openssl rand -hex 32)
sed -i "s/__BRAINZMASH_KEY__/$KEY/" local/compose/brainzmash/nginx.conf
echo "Generated BrainzMash key: $KEY"
```

- Share the key (privately) with the brainzmash operator


## 3. Register compose

- Adds the nginx compose to .env

```
admin/configure add local/compose/brainzmash-nginx.yml
```

## 4. Start new service

```
docker compose up -d
```

- Check docker, you should now see a new container 'musicbrainz-docker-brainzmash-nginx'

- Change your share (cloudflare, or similar) to share port 5002 (the NGINX container) 
