# marimo-runtime

Fork this, deploy it, get your own interactive [marimo](https://marimo.io)
notebook running in the cloud on **Aiven Runtimes** — no database, no
extra services required.

## What's here

- `notebook.py` — a placeholder marimo notebook. Replace it with your own.
- `Dockerfile` — builds and serves it with `marimo edit`, gated behind a
  token password.
- `requirements.txt` — just `marimo`.

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

```bash
pip install -r requirements.txt
marimo edit notebook.py
```

## Deploy it on Aiven Runtimes

Aiven Runtimes (Aiven Applications) builds and runs this `Dockerfile`
straight from your fork:

1. Push your fork to GitHub (public, or connect the account under
   **Aiven Console → your project → Integrations → GitHub** if private).
2. Create the application service — plan `free-10-256` is enough for a
   single notebook — pointing at your repo/branch, port `8080`.
3. Set an environment variable `MARIMO_TOKEN_PASSWORD` (as a secret) —
   this is the password required to open the notebook, since editable
   mode allows running arbitrary code for anyone who reaches the URL.

No database or other service integration needed for this template.

## Other examples

- `examples/postgres-persistence/` — the same idea, but the notebook's
  widget state and a change history are persisted to a real
  **Aiven for PostgreSQL** service instead of only living in memory.
  Useful if you want your notebook's state to survive restarts.
