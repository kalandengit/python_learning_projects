# VPS deployment

Odoo runs in Docker bound to `127.0.0.1`; the host's Nginx publishes it. Other
projects on the same VPS keep their own vhosts and ports untouched.

## First deployment

1. `cp .env.example .env` and replace every `CHANGE_ME`
   (`openssl rand -base64 36`). Pick an `ODOO_PORT` no other project uses.
2. `./scripts/validate-stack.sh` — offline checks: config rendering, refusal of
   placeholder secrets, `nginx -t`, `docker compose config`, secret scan.
3. `./scripts/preflight.sh` — shows host state: disk, memory, listening ports,
   existing containers and vhosts.
4. `./scripts/deploy.sh` — renders `generated/odoo.conf` (0600), pulls images
   and starts the stack.
5. Point DNS at the VPS, then `sudo ./scripts/install-nginx.sh` — verifies DNS
   actually resolves here before asking certbot for a certificate, then
   installs the TLS vhost.
6. Create the database named in `ODOO_DB` through the controlled setup path.
7. `./scripts/install-modules.sh "$ODOO_DB"` — installs `ems_suite`.
8. `sudo ./scripts/install-logrotate.sh` — installs the host logrotate policy
   for the container's log volume.
9. **Run a restore drill before launch** (below). A backup you have never
   restored is not a backup.

## Routine operations

| Task | Command |
| --- | --- |
| Backup (database + filestore + checksums) | `./scripts/backup.sh` |
| Upgrade EMS (takes a rollback point first) | `./scripts/update-modules.sh` |
| Restore | `./scripts/restore.sh <db-….dump> [<filestore-….tar.gz>]` |
| Re-validate the stack after edits | `./scripts/validate-stack.sh` |

`backup.sh` writes `db-<stamp>.dump`, `filestore-<stamp>.tar.gz` and a single
`backup-<stamp>.sha256` covering both, into `BACKUP_DIR` (0700), pruning files
older than `BACKUP_RETENTION_DAYS`. Ship these off-host; a backup living only
on the machine it protects is not a backup either.

`restore.sh` **refuses** to run without a matching checksum sidecar, stops Odoo
before `pg_restore --clean` (which cannot drop objects a live server holds
open), restores the filestore if given, and restarts.

## Restore drill

```bash
./scripts/backup.sh                       # note the printed paths
./scripts/restore.sh /var/backups/ems-odoo/db-<stamp>.dump \
                     /var/backups/ems-odoo/filestore-<stamp>.tar.gz
docker compose --env-file .env exec -T odoo \
  odoo -d "$ODOO_DB" -u ems_suite --stop-after-init   # prove it still upgrades
```

Then log in and open **EMS → Tickets**. A restore that loads rows but produces
a database Odoo cannot upgrade has not succeeded. This drill was executed
against the test database during development; see
`../docs/INSTALL_TEST_REPORT.md` §5.

## Rollback

`update-modules.sh` always takes a backup first and prints the exact
`restore.sh` command to undo the upgrade. Keep the pre-upgrade dump until the
new version has run a full event.

## What the stack guarantees

* Odoo listens on `127.0.0.1:${ODOO_PORT}` only — never on a public interface.
* PostgreSQL publishes no host port at all.
* `list_db = False` and `dbfilter = ^${ODOO_DB}$`: the database manager is
  closed and only the configured database is served.
* TLS 1.2/1.3 with HSTS; `/websocket` proxied with the upgrade headers Odoo's
  bus requires; the scanner's service worker served uncached.
* Container logs capped by the json-file driver (10 MB × 5); the Odoo log file
  rotated daily by the host, kept 30 days, compressed, using `copytruncate`
  because the process holds the file open.
* Both container services restart automatically and expose healthchecks.

## Note on the Odoo image

`docker-compose.yml` pins `odoo:19.0`. The addons directory is mounted
read-only at `/mnt/extra-addons`. If you build a custom image instead, keep the
addons path and use Odoo's own pinned `requirements.txt`.
