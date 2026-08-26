# marimo-runtime

Fork this, deploy it, get your own interactive [marimo](https://marimo.io)
notebook running in the cloud on **Aiven Runtimes** — no database, no
extra services required, and every visitor gets their own private,
editable copy of the notebook.

## How the per-visitor isolation works

The `Dockerfile` doesn't run a marimo server. Instead it exports
`notebook.py` to a self-contained WASM build (`marimo export html-wasm
--mode edit`) at image-build time, and serves the resulting static
files. Each visitor's browser then runs its own [Pyodide](https://pyodide.org)
(Python-in-WebAssembly) instance locally:

- No shared server-side kernel, so visitors can't see or overwrite
  each other's edits — everyone gets an independent copy of the notebook.
- No arbitrary code ever runs on the container itself, since all
  execution happens client-side in the visitor's own browser sandbox.
  There's no token/password to manage as a result.
- Trade-offs: the container serves tens of MB of Pyodide/WASM assets on
  first load (nginx gzips these in flight — see below — but it's still
  a real download), Pyodide supports most but not all PyPI packages
  (see the [Pyodide package list](https://pyodide.org/en/stable/usage/packages-in-pyodide.html)),
  and nothing a visitor edits is persisted anywhere — closing the tab
  loses their changes, by design (their copy, their session).

## What's here

- `notebook.py` — a placeholder marimo notebook. Replace it with your own.
- `Dockerfile` — exports `notebook.py` to WASM at build time, then a
  second stage serves the static output with nginx.
- `nginx.conf` — gzip and long-lived caching for the content-hashed
  asset files, so the (large) first load is smaller and repeat visits
  are near-instant. Plain `python -m http.server` does neither, which
  makes the difference between an okay first load and a very slow one.
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

- `examples/postgres-persistence/` — a single shared, server-backed
  notebook (via `marimo edit`/`marimo run`, not WASM) whose widget state
  and change history persist to a real **Aiven for PostgreSQL** service.
  Unlike the root template, all visitors share one notebook instance —
  useful if you want state to survive restarts rather than isolating
  each visitor.
