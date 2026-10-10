# Monopoly Vault

A mobile-first web app that lets a household pool their McDonald's Monopoly codes in one place, see which
color sets are complete, and redeem them without double-submitting.

- **Add codes by photo.** Take a picture of the sticker. Tesseract OCR reads the code, you confirm or fix
  it, and the original photo is kept with the code.
- **Collection board.** See every color set and piece, for the whole household or just you, and exactly
  which pieces are missing.
- **Vaults.** Family members join one shared vault with an invite code. Codes are shared by default and can
  be made private, one code at a time.
- **Copy to redeem.** One tap copies a code and marks it *Pending* so nobody else copies it. The next time you
  open the app, it asks whether you submitted it.
- **Ready-to-redeem alerts** when a set is complete.
- **Help everywhere.** Each section has an (i) button that explains how it works.
- **Installable PWA.** Add it to your phone's home screen.

## What it does not do

Monopoly Vault only keeps track of codes and gives you a copy button. It never signs in to, automates, or
submits anything to the McDonald's app, and it has no feature that moves codes between people's McDonald's
accounts. Under the 2026 Official Rules, each person redeems from their own McDonald's account, and original
physical stickers must be kept for Collect to Win prizes. McDonald's allows 8 code entries per day per account,
and prize claims close November 22, 2026. The app shows both as reminders.

## Quick start

You need Docker with the Compose plugin (`docker compose version` should work).

```sh
git clone <this repo> monopoly-vault
cd monopoly-vault
cp .env.example .env
```

Edit `.env` and replace the two `CHANGE ME` values. You can generate them like this:

```sh
sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$(openssl rand -hex 16)/" .env
sed -i "s/^JWT_SECRET=.*/JWT_SECRET=$(openssl rand -hex 32)/" .env
```

Start everything:

```sh
docker compose up -d --build
```

Open **http://localhost:1023**, create an account, then create a vault on the **Vault** tab and send the
invite code to your family.

When everyone has an account, set `ALLOW_SIGNUP=false` in `.env` and run `docker compose up -d` again to
turn off new sign-ups.

Check that the services are healthy with `docker compose ps`. To stop the app, run `docker compose down`.
Your data is kept in Docker volumes.

## Services

| Service | What it is | Exposed |
| --- | --- | --- |
| `web` | nginx serving the React PWA; proxies `/api` to `api` | Host port **1023** (container port 80) |
| `api` | FastAPI with Tesseract OCR; runs database migrations on start | Internal only |
| `db` | PostgreSQL 16 | Internal only |

All three have healthchecks and `restart: unless-stopped`. The API docs are at http://localhost:1023/api/docs.

## Settings (`.env`)

| Variable | Default | What it does |
| --- | --- | --- |
| `POSTGRES_USER` | `vault` | Database user |
| `POSTGRES_DB` | `vault` | Database name |
| `POSTGRES_PASSWORD` | *(required)* | Database password |
| `JWT_SECRET` | *(required)* | Signs login tokens. Changing it signs everyone out. |
| `JWT_EXPIRE_HOURS` | `720` | How long a login lasts (30 days) |
| `ALLOW_SIGNUP` | `true` | Whether the sign-in screen offers "Create account" |
| `CAMPAIGN_YEAR` | `2026` | Which season file is active (`api/app/seasons/<year>.json`) |
| `PHOTOS_PATH` | `photos` | Where sticker photos are stored (see below) |
| `MAX_UPLOAD_MB` | `12` | Largest photo accepted |

`.env` is ignored by git. Only `.env.example` is committed.

## Photo storage (and moving it to a NAS)

Original sticker photos are stored as files. The database only stores each file's path, relative to the
photo folder. Inside the `api` container the folder is always `/data/photos`. `PHOTOS_PATH` decides what is
mounted there:

- `PHOTOS_PATH=photos` (the default) uses a Docker named volume called `monopoly-vault_photos`.
- `PHOTOS_PATH=/absolute/path` uses that folder on the host, for example a NAS share that is already mounted
  on the host.

To switch to a NAS:

1. Mount the share on the Docker host, for example at `/mnt/nas/monopoly-vault/photos`.
2. The API runs as uid 1000, so make sure that uid can write there:
   `sudo chown -R 1000:1000 /mnt/nas/monopoly-vault/photos`. For SMB/CIFS mounts, use `uid=1000,gid=1000`
   in the mount options instead.
3. If you already have photos in the named volume, copy them over:
   ```sh
   docker run --rm -v monopoly-vault_photos:/from -v /mnt/nas/monopoly-vault/photos:/to alpine cp -a /from/. /to/
   ```
4. Set `PHOTOS_PATH=/mnt/nas/monopoly-vault/photos` in `.env` and run `docker compose up -d`.

Files are laid out as `<year>/user-<id>/<random>.jpg`. A photo that was uploaded and then cancelled before
saving stays in the folder unused. You can safely delete those.

## Using it on phones

Open `http://<server-ip>:1023` from a phone on the same network. Browsers only allow the service worker
(home-screen install and offline shell) and the modern clipboard API on **HTTPS** or `localhost`. Over plain
http on a LAN address, the app still works and the copy button falls back to an older method. For the full
experience, put it behind your reverse proxy with a certificate, for example `monopoly.example.com`
pointing to `http://<docker-host>:1023`.

## How redemption tracking works

```
Available --tap Copy--> Pending --"Yes, I submitted it"--> Used (final, timestamped, who used it)
                           \--"No"------------------------> Available
```

- Only an **Available** code can be copied. Copying is an atomic database update, so if two people tap Copy
  at the same moment, only one gets the code. Whoever copied a Pending code can copy it again. Everyone else
  waits until it is answered.
- A *session* lasts as long as the browser tab or home-screen app stays open. On the next session, the app
  asks about each code you copied earlier that is still Pending. "Ask me later" leaves it Pending.
- The daily counter shows how many codes you've copied today (in your time zone), against McDonald's limit
  of 8.

**Privacy.** Codes are Shared by default. Shared codes are visible to everyone in your vault and count in the
Household view. A Private code is visible only to you and counts only in your *Mine* view. It never appears in
the pooled Household view.

**Set completion.** A piece is held when it has at least one Available or Pending code. Used codes no
longer count. A set is ready when every piece in it is held.

## A new season

Each October campaign is its own season, and nothing carries over between years.

1. Copy `api/app/seasons/2026.json` to `api/app/seasons/<year>.json` and update the pieces, the winning
   combinations (`sets`), `daily_entry_limit`, `claim_deadline` and, if the code format changed,
   `code_pattern` (a regular expression for a code after spaces and dashes are removed).
2. Set `CAMPAIGN_YEAR=<year>` in `.env` and run `docker compose up -d --build`.

Vaults and codes are stored per year, so everyone starts the new season with an empty board and creates or
joins a vault again.

## Tests

The backend tests cover the status flow (Available, Pending, Used), the privacy rules, set completion, vaults,
and OCR/photo handling. They use an in-memory SQLite database, so they don't need Postgres.

```sh
docker compose run --rm --no-deps api pytest
```

Or, without Docker, from the `api` folder (Python 3.12):

```sh
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Development

- **Backend:** `api/app`. Routes are in `routers/`, rules in `services/` (`codes.py` for the status flow,
  `privacy.py`, `collection.py`, `vaults.py`, `ocr.py`, `photos.py`).
- **Database migrations:** after changing `api/app/models.py`, generate a migration with
  ```sh
  docker compose run --rm -v "$PWD/api:/app" api alembic revision --autogenerate -m "describe the change"
  ```
  Review the new file in `api/alembic/versions/`. Migrations are applied automatically when the API starts.
- **Frontend:** `web/src` (React and Vite, no UI framework). For hot reload, publish the API port by adding
  `ports: ["8000:8000"]` to the `api` service in a `docker-compose.override.yml`, then run
  `cd web && npm install && npm run dev`.
- **Help text** for every (i) button is in `web/src/help.jsx`.

## Backups

Back up the database and the photo folder together:

```sh
docker compose exec db pg_dump -U vault vault > monopoly-vault-$(date +%F).sql
```

Then back up the photo folder: either the `PHOTOS_PATH` folder, or the `monopoly-vault_photos` volume.

## Project layout

```
docker-compose.yml   .env.example
api/                 FastAPI app, Alembic migrations, season files, tests
web/                 React PWA, nginx config, service worker, manifest
```
