# Update to be run before Brainzmash schema change and PG18 update - v-2026-05-13.0-mbdb31-pg18

- the Musicbrainz update assumes the install user of the database is 'musicbrainz', while the original LMD setup used user 'abc' so we'll change LMD to make it use the musicbrainz user and rename the db user to keep Musicbrainz updater happy and make things future-proof.

## 1. Pull latest LMD image

- From within your Musicbrainz docker folder. This changes the db username that lmd uses from abc to musicbrainz.

```
docker compose pull lmd
docker compose up -d --force-recreate lmd
```


## 2. Edit lmd-settings.yml 


```
nano local/compose/lmd-settings.yml 
```
- Remove the md & redis lines from the depends_on section. (Leave valkey out for now, easier to leave it out and add it later so the update instructions work without hassle). Should look like:

```
    depends_on:
      - db
      - search
```

- Change REDIS_HOST to valkey

```
       REDIS_HOST: "valkey"
```


## 3. Rename 'abc' db user to 'musicbrainz'

- Check users, you should just have abc as that's how it was originally set up with LMD:

```
docker compose exec db psql -U abc -d postgres -c "\du"
```

- This should be what you have:

```
                             List of roles
 Role name |                         Attributes                         
-----------+------------------------------------------------------------
 abc       | Superuser, Create role, Create DB, Replication, Bypass RLS
```

- Create a temp admin so we can rename the abc user

```
docker compose exec db psql -U abc -d postgres
```

```
CREATE ROLE tempadmin
WITH LOGIN
SUPERUSER
PASSWORD 'tempadmin';
\q
```

- Connect as the temp

```
docker compose exec db psql -U tempadmin -d postgres
```

- Rename abc and change password

```
ALTER ROLE abc RENAME TO musicbrainz;
ALTER ROLE musicbrainz PASSWORD 'musicbrainz';
```

- Connect as musicbrainz and drop the temp role

```
DROP ROLE tempadmin;
\q
```

- Check result

```
docker compose exec db psql -U musicbrainz -d postgres -c "\du"
```

- You should have this:

```
                                List of roles
    Role name    |                         Attributes                         
-----------------+------------------------------------------------------------
 musicbrainz     | Superuser, Create role, Create DB, Replication, Bypass RLS
```


## 4. BACKUP FIRST!!

- I found Musicbrainz' update script a little fragile, if there's an issue you'll end up in a broken state - should be ok unless you've strayed from defaults.

## 5. Follow Musicbrainz' update instructions

- https://github.com/metabrainz/musicbrainz-docker/releases/tag/v-2026-05-11.0-mbdb31-pg18


Note, make sure to answer no to this
```
Volume "musicbrainz-docker_pgdata" exists but doesn't match configuration in compose file. Recreate (data will be lost)? No
```

- When all steps are completed, carry on with the below.


## 6. Add valkey to LMD compose

```
nano local/compose/lmd-settings.yml 
```

```
    depends_on:
      - db
      - search
      - valkey
```

## 7. Run full replication

```
docker exec -it musicbrainz-docker-musicbrainz-1 \
/usr/local/bin/replication.sh
```

## 8. Test LMD

- This should return replication date:

```
curl 127.0.0.1:5001
```

- This should return an artist lookup:

```
curl 127.0.0.1:5001/artist/936addc3-91aa-49de-8ec0-0dc186de151f
```

### 9. Done!
