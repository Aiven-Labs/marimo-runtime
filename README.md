# marimo + Aiven for PostgreSQL

A small demo showing [marimo](https://marimo.io) (a reactive Python
notebook) using a real **Aiven for PostgreSQL** service as its storage
backend, instead of keeping widget state only in notebook memory.

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

## Aiven setup already done

A PostgreSQL 17 service called `marimo-demo-pg` is running in the
`hevans-demo` Aiven project (`aws-eu-west-1`, `startup-4` plan). The
`app_state` and `state_history` tables (see `schema.sql`) already exist
on it. If you want to point this at a different Postgres instance, just
run `schema.sql` against it — everything else works unchanged.

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and fill in `PGPASSWORD` — grab it from the Aiven Console
(**Services → marimo-demo-pg → Overview → Connection information**) or
via the CLI:

```bash
avn service get marimo-demo-pg --project hevans-demo -v
```

Then start the notebook:

```bash
marimo edit app.py     # interactive editor
# or
marimo run app.py      # read-only app view
```

## Deploying marimo itself onto Aiven (Aiven Applications)

To have marimo running as a hosted service on Aiven (not just Postgres),
Aiven's "Applications" product builds and runs a Dockerized app straight
from a GitHub repo. This repo already includes the `Dockerfile` for that.

```bash
git checkout -b marimo-demo   # or whatever branch you want to deploy from
git add app.py Dockerfile .dockerignore schema.sql requirements.txt README.md .env.example
git commit -m "Add marimo + Aiven Postgres demo"
git push origin marimo-demo
```

Because `Aiven-Labs/marimo-runtime` is private and no GitHub account
connected to the `hevans-demo` Aiven project currently has access to it,
Aiven can't pull it yet. In the Aiven Console: **Integrations → GitHub**,
connect the GitHub account that has access to `Aiven-Labs/marimo-runtime`.
Once that's done, tell me the branch name and I can deploy with
`aiven_application_deploy` — it will:

- pull and build this `Dockerfile` (exposes port `8080`),
- attach `marimo-demo-pg` as a service integration so `DATABASE_URL` is
  injected automatically (no manual `.env` needed in production),
- run `marimo edit` behind a token password (`MARIMO_TOKEN_PASSWORD`,
  passed as a deploy-time secret) rather than the open `marimo run` view,
  since editable mode allows arbitrary code execution for anyone who has
  the URL and password.

Still to decide: which Application plan (`free-10-256` at no cost, or a
paid `startup-*` tier) and which cloud region.

## Files

- `app.py` — the marimo notebook/app.
- `schema.sql` — the two Postgres tables the app uses.
- `requirements.txt` — `marimo`, `psycopg[binary]`, `python-dotenv`.
- `.env.example` — connection settings template (no real secrets).
- `Dockerfile` / `.dockerignore` — container image for Aiven Applications.

## Notes for reuse

- Aiven services require TLS (`sslmode=require`); already set in
  `.env.example`.
- `marimo-demo-pg` is on the `startup-4` plan (~$0.15/hr). Power it off
  or delete it from the Aiven Console when you're done demoing to stop
  charges — the free and hobbyist tiers were unavailable on this
  organization's token when this was built.
- If/when deployed as an Aiven Application, that service has its own
  running cost too (`free-10-256` is free; `startup-*` tiers are not) —
  stop or delete it from the Console when you're done.
