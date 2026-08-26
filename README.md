# marimo-runtime

Fork this, deploy it, get your own interactive [marimo](https://marimo.io)
notebook running in the cloud on **Aiven Runtimes**. No database, no
extra services required, and every visitor gets their own private,
editable copy of the notebook.

## How the per-visitor isolation works

The `Dockerfile` doesn't run a marimo server. Instead it exports
`notebook.py` to a self-contained WASM build (`marimo export html-wasm
--mode edit`) at image-build time, and serves the resulting static
files. Each visitor's browser then runs its own [Pyodide](https://pyodide.org)
(Python-in-WebAssembly) instance locally, meaning:

- No shared server-side kernel, so visitors can't see or overwrite
  each other's edits *everyone gets an independent copy of the notebook*.
- No arbitrary code ever runs on the container itself, since all
  execution happens client-side in the visitor's own browser sandbox.
  There's no token/password to manage as a result.
- The container serves tens of MB of Pyodide/WASM assets on
  first load which can be a little slow (nginx gzips these in flight but it's still
  a real download).
- Pyodide supports most but not all PyPI packages
  (see the [Pyodide package list](https://pyodide.org/en/stable/usage/packages-in-pyodide.html)),
- Nothing a visitor edits is persisted anywhere so closing the tab
  loses their changes, see examples for how Postgres can be used to persist user sessions.

## What's here

- `notebook.py` — a placeholder marimo notebook. Replace it with your own.
- `temperature_converter.py` — a second, unrelated notebook, here to
  demo [Multiple notebooks](#multiple-notebooks) below rather than to be
  useful on its own. Delete it if you only want the one notebook.
- `export_notebooks.py` — finds every notebook in this directory and
  exports each to WASM at build time; see below.
- `Dockerfile` — runs `export_notebooks.py` at build time, then a
  second stage serves the static output with nginx.
- `nginx.conf` — gzip and long-lived caching for the content-hashed
  asset files, so the (large) first load is smaller and repeat visits
  are near-instant.
- `requirements.txt` — just `marimo` (only needed to run the export).

That's the whole template. `examples/` has more involved variants (see
below).

## Use your own notebook

**Starting a marimo notebook from scratch:** edit `notebook.py` directly,
or run `marimo edit notebook.py` locally to build it interactively.

**Bringing an existing Jupyter/IPython notebook:** marimo can convert a
`.ipynb` file straight to marimo's format:

```bash
pip install marimo
marimo convert your_notebook.ipynb -o notebook.py
```

Marimo's execution model is reactive (cells rerun automatically based on
what they depend on), which differs from Jupyter's run-cells-in-any-order
model — the conversion handles the mechanical part, but notebooks that
mutate the same variable across multiple cells may need small tweaks
afterward. `marimo edit notebook.py` locally is the fastest way to check.

## Multiple notebooks

`temperature_converter.py` is here to demonstrate this: drop another
`.py` notebook into this directory (or `examples/postgres-persistence/`)
and it's picked up automatically — `export_notebooks.py` finds every
file that defines `marimo.App(...)`, no Dockerfile edit needed.

marimo doesn't have a built-in way to navigate between separate WASM
exports — each one is a fully self-contained Pyodide bundle with no
shared runtime or file browser (that's a server-only feature of
`marimo edit`). So: with exactly one notebook, this deploys exactly as
before, straight at `/`. With more than one, each gets its own
subdirectory (e.g. `/second-notebook/`) and the site root becomes a
plain, static links page — the same pattern marimo's own multi-notebook
deployment guide recommends, not a custom router.

## Run it locally

As a normal server-backed notebook, for fast iteration while you build:

```bash
pip install -r requirements.txt
marimo edit notebook.py
```

To preview exactly what visitors will get (the WASM build):

```bash
marimo export html-wasm notebook.py -o /tmp/site --mode edit
python -m http.server 8080 --directory /tmp/site
# open http://localhost:8080
```

With more than one notebook in the directory, run `export_notebooks.py`
instead — it reproduces exactly what the Dockerfile does, including the
links page:

```bash
pip install marimo
python export_notebooks.py /tmp/site
python -m http.server 8080 --directory /tmp/site
```

## Deploy it on Aiven Runtimes

Aiven Runtimes (Aiven Applications) builds and runs this `Dockerfile`
straight from your fork:

1. Push your fork to GitHub (public, or connect the account under
   **Aiven Console → your project → Integrations → GitHub** if private).
2. Create the application service — plan `free-10-256` is enough for a
   single notebook — pointing at your repo/branch, port `8080`.

No environment variables, database, or other service integration needed
for this template.

## Other examples

- `examples/postgres-persistence/` — same per-visitor WASM isolation as
  this root template, plus real persistence: each visitor's widgets are
  saved to a real **Aiven for PostgreSQL** service, keyed by an
  anonymous id stored in their browser, and reload exactly where they
  left off. A tiny bundled API bridges the browser-side notebook to
  Postgres (Pyodide can't open a raw database connection itself).
