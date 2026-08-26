# marimo + Aiven for PostgreSQL: isolated *and* persisted

A variant of the root [`notebook.py`](../../notebook.py) template that
keeps the root template's per-visitor isolation, and adds real
persistence on top: every visitor's widgets survive a page reload,
because they're saved to a real **Aiven for PostgreSQL** service instead
of only living in a Python process.

## What it shows

Like the root template, `notebook.py` here exports to WASM — every
visitor's browser runs its own private [Pyodide](https://pyodide.org)
(Python-in-WebAssembly) instance. On top of that:

1. On first visit, the notebook generates a random id and stores it in
   *your browser's* `localStorage`. No login — "this browser" is the
   identity.
2. The notebook loads any state saved under that id from Postgres (via
   a small bundled API — see below), and uses it as the widgets'
   initial values.
3. Every widget change is sent to that same API, which upserts it into
   an `app_state` table (keyed by your browser id) and appends a row to
   a `state_history` audit table.
4. Reload the page in the same browser and your widgets come back
   exactly where you left them. Open it in a different browser or an
   incognito window and you get a brand-new, empty session — your data
   is yours alone.

## Why there's a bundled API

Pyodide can't open a raw TCP socket, so the in-browser notebook can't
speak Postgres wire protocol directly — only HTTP. This example bundles
a second, tiny process (`api.py`, stdlib `http.server`, no framework)
into the *same* container as the nginx-served WASM site:

- nginx serves the static WASM/Pyodide bundle, and reverse-proxies
  `/api/*` to `api.py`.
- `api.py` binds to `127.0.0.1` only — it's never reachable directly
  from outside the container, only through nginx.
- It exposes exactly two things: `GET/POST /api/state/<id>` and
  `GET /api/history/<id>`, each scoped to the id in the URL. It accepts
  structured JSON, not code — there's no arbitrary-execution surface
  the way a real `marimo edit` server would have.

That last point is why this example needs no password, unlike an
earlier version of it: nothing here runs a visitor's Python on the
server. All notebook code still executes client-side, in each visitor's
own Pyodide sandbox — `api.py` is just a narrow, fixed-behavior data
bridge.

One Aiven Application, one container, one deploy — same as the root
template.

## Run it locally

Full local preview needs both halves running:

```bash
cd examples/postgres-persistence
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL
python api.py &        # binds 127.0.0.1:8000
marimo export html-wasm notebook.py -o /tmp/site --mode edit
python -m http.server 8080 --directory /tmp/site
# open http://localhost:8080 -- note this preview talks to api.py over
# plain HTTP without nginx's reverse proxy in front of it
```

Point `.env` at any PostgreSQL instance (an Aiven for PostgreSQL service
works well); `api.py` creates `app_state` and `state_history` itself on
first run (see `schema.sql` if you'd rather apply it by hand).

You can also just run `marimo edit notebook.py` for fast iteration on
the notebook itself — outside Pyodide it falls back to plain
`urllib.request` against `api.py` on `127.0.0.1:8000`, so start `api.py`
first if you want the save/load calls to succeed rather than silently
falling back to defaults.

## Deploying as an Aiven Application

This folder's `Dockerfile` is a two-stage build:

1. Exports `notebook.py` to a static WASM bundle at image-build time
   (same as the root template).
2. A runtime image with both nginx (serving the bundle, proxying
   `/api/`) and Python (running `api.py`) — needs `psycopg`, so this
   stage stays on Debian/glibc (`python:3.11-slim` + `apt-get install
   nginx`) rather than `nginx:alpine`.

Attach a Postgres service integration (`application_service_credential`)
so Aiven injects `DATABASE_URL` at runtime — no manual credential
handling needed, and the app and database must be in the same Aiven
project for this integration type. Build path for the deploy needs to
point here, e.g. `build_path: examples/postgres-persistence` if
deploying straight from this repo.

## Files

- `notebook.py` — the marimo notebook, exported to WASM. Generates the
  per-browser id and calls the bundled API to load/save state.
- `api.py` — the internal API bridging Pyodide to Postgres.
- `nginx.conf` — serves the static site and reverse-proxies `/api/` to
  `api.py`; same gzip/MIME setup as the root template's config.
- `start.sh` — starts `api.py` in the background, then execs nginx as
  the container's main process.
- `schema.sql` — the two Postgres tables (`api.py` also creates these
  itself on startup).
- `requirements.txt` — `marimo`, `psycopg[binary]`, `python-dotenv`
  (covers both local notebook preview and running `api.py` locally).
- `.env.example` — `DATABASE_URL` template for local `api.py` runs (no
  real secrets).
- `Dockerfile` / `.dockerignore` — the two-stage container image.

## Notes

- Data is only as anonymous as `localStorage` — clearing browser data,
  or visiting from a different browser/device, starts a fresh session
  with no way to recover the old one. There's no login layer here.
- Whatever Postgres service and Application service you deploy this
  against have their own running costs — stop or delete them from the
  Aiven Console when you're done with a given demo.
