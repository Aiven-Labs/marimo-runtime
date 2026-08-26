# marimo + Aiven for PostgreSQL

A variant of the root [`notebook.py`](../../notebook.py) template that
persists its state to a real **Aiven for PostgreSQL** service instead of
only keeping it in notebook memory.

## What it shows

The notebook (`app.py`) has four interactive widgets (a slider, a
dropdown, a text field, a checkbox). Every time one changes:

1. marimo's reactive execution model reruns the cell that depends on
   the widget's `.value`.
2. That cell writes the new value into an `app_state` table in Postgres
   (an upsert) and appends a row to a `state_history` audit table.
3. A later cell reads `state_history` straight back from Postgres and
   displays it.

Restart the notebook (or `marimo edit` again after quitting) and the
widgets reload their last saved values from Postgres — proving the
state lives in the database, not in the Python process.

## Run it locally

```bash
cd examples/postgres-persistence
pip install -r requirements.txt
cp .env.example .env
```

Point `.env` at any PostgreSQL 17 instance (an Aiven for PostgreSQL
service works well) and run `schema.sql` against it once to create the
two tables. Then:

```bash
marimo edit app.py     # interactive editor
# or
marimo run app.py      # read-only app view
```

## Deploying as an Aiven Application

This folder's `Dockerfile` builds and runs `app.py` the same way the
root template does. The one difference is a Postgres service integration
(or plain `PGHOST`/`PGUSER`/... environment variables) so `DATABASE_URL`
is available at runtime — `app.py` reads `DATABASE_URL` first and falls
back to individual `PG*` vars if it's unset.

Build path for the deploy needs to point here, e.g.
`build_path: examples/postgres-persistence` if deploying straight from
this repo.

## Files

- `app.py` — the marimo notebook/app.
- `schema.sql` — the two Postgres tables the app uses.
- `requirements.txt` — `marimo`, `psycopg[binary]`, `python-dotenv`.
- `.env.example` — connection settings template (no real secrets).
- `Dockerfile` / `.dockerignore` — container image for this example.

## Notes

- Aiven services require TLS (`sslmode=require`); already set in
  `.env.example`.
- Whatever Postgres service and Application service you deploy this
  against have their own running costs — stop or delete them from the
  Aiven Console when you're done with a given demo.
