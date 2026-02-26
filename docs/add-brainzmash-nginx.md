# Add Brainzmash Nginx proxy

## 1. Create brainzmash-nginx.yml

- From within your Musicbrainz docker folder

```
nano /local/compose/brainzmash-nginx.yml
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
nano /local/compose/brainzmash/nginx.conf
```

- Paste

```
worker_processes auto;

events {
    worker_connections 1024;
}

http {

    # Optional small rate limit protection
    limit_req_zone $binary_remote_addr zone=brainzmash:10m rate=10r/s;

    server {
        listen 80;

        # Inserted by setup script
        set $expected_key "__BRAINZMASH_KEY__";

        location / {

            # Require correct BrainzMash header
            if ($http_x_brainzmash_key != $expected_key) {
                return 403;
            }

            # Light rate limiting
            limit_req zone=brainzmash burst=20 nodelay;

            proxy_pass http://lmd:5001;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }
    }
}
```

- Save

## 2.1 Generate and insert API key

- Generate sand insert key

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
