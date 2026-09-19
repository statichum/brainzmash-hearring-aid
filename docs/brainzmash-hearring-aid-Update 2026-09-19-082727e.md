# brainzmash-hearring-aid LMD update - Applies to: `082727e'

LMD has been updated, two main changes:
- The original Album artwork selection for Musicbrainz' Cover Art Archive images was flawed and wasnt honouring the main image selected for the Release Group on Musicbrainz 
- Artist posters now use Deezer as an alternative when images are not available elsewhere which fills a lot of artist image gaps. The Artist must have their Deezer link in 'External Links' on the Musicbrainz artist page.

Run these commands on each MusicBrainz backend server.

## 1. Open the MusicBrainz Docker directory

e.g.
```
cd /docker/musicbrainz-docker
```

## 2. Just to be sure let's test an artist before and after

(Should have no image)

```
ARTIST='928347ec-58f4-499c-a629-9ac4ca07db6d'

curl -fsS -X POST \
  "http://127.0.0.1:5001/artist/$ARTIST/refresh" |
  jq .

curl -fsS \
  "http://127.0.0.1:5001/artist/$ARTIST" |
  jq '{artistname, images}'
```


## 3. Update

```cd /docker/musicbrainz-docker

docker build \
  -t statichum/brainzmash-hearring-aid:latest \
  'https://github.com/statichum/brainzmash-hearring-aid.git#main'

docker compose up -d --pull never --no-deps --force-recreate lmd

```

## 4. Re-test that artist

(Should now have an image!)

```ARTIST='928347ec-58f4-499c-a629-9ac4ca07db6d'

curl -fsS -X POST \
  "http://127.0.0.1:5001/artist/$ARTIST/refresh" |
  jq .

curl -fsS \
  "http://127.0.0.1:5001/artist/$ARTIST" |
  jq '{artistname, images}'
```

## 5. Flush Artist Caches

```docker compose exec -T db psql \
  -U musicbrainz \
  -d lm_cache_db \
  -c 'TRUNCATE TABLE artist;'
```

## Done!
