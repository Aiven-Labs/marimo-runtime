# marimo, shared and password-protected

A different trade-off from the root template: instead of exporting to
WASM so every visitor gets an isolated, sandboxed copy, this example
runs a real `marimo edit` server. One live Python kernel, one
`notebook.py` file, shared by everyone who has the password. Edit a
cell and save it (`Ctrl+S`, or just wait for autosave) and the change
is on disk for real -- not just in your own browser tab.

## What it shows

- `marimo edit notebook.py --host 0.0.0.0 --port 8080 --headless
  --token-password "$MARIMO_TOKEN_PASSWORD"` is the entire deployment --
  no WASM export step, no nginx, no bundled API, no Postgres. marimo's
  own server does everything: serves the UI, runs the kernel, and (per
  [marimo's authentication guide](https://docs.marimo.io/guides/deploying/authentication/))
  gates access behind a token/password out of the box.
- Saving is real and native here, unlike the WASM examples: `Ctrl+S` (or
  autosave) writes straight to `notebook.py` on disk, because there's an
  actual filesystem and an actual `marimo edit` process behind it. No
  custom code needed for that -- it's not a feature of this template,
  it's just what `marimo edit` always does.
- Open the page in two tabs and edit different cells in each: both see
  each other's changes, because it's one shared kernel and one shared
  file, not two private copies.

## The trade-off, plainly

This is the opposite security model from the root template's WASM
export, and worth reading before you deploy it anywhere real:

- **No sandbox.** Anyone who knows the password can read, edit, and run
  arbitrary Python in this container -- including anything reachable
  from it (environment variables, attached services, the network). The
  password is the *entire* access control. Don't attach this to a
  database or credentials you wouldn't hand to whoever you share the
  password with.
- **No per-visitor isolation.** Everyone shares one kernel and one file.
  A long-running cell blocks the notebook for everyone, not just
  whoever started it. Two people editing the same cell at the same time
  will conflict the way two people editing the same file always do.
- **The container's filesystem is not persistent storage.** Aiven
  Applications don't give this template a mounted volume, so whatever
  gets saved to `notebook.py` lives only as long as this specific
  running container does -- a redeploy or restart starts fresh from
  whatever's in the image (i.e. whatever was last committed to the
  repo), not from what was last saved live. Treat live edits here as
  session-length, not durable, unless you add your own persistent
  volume or a step that commits changes out somewhere.
- marimo's own token-password auth is intentionally simple (see its
  [authentication guide](https://docs.marimo.io/guides/deploying/authentication/))
  -- no per-user accounts, no rate limiting, no audit log of who changed
  what. That's a reasonable fit for "a few trusted people share a
  notebook," not for anything wider.

## Run it locally

```bash
cd examples/shared-server
pip install -r requirements.txt
marimo edit notebook.py --token-password "pick-something"
# opens http://localhost:2718?access_token=pick-something
```

Or without a password, for quick local iteration:

```bash
marimo edit notebook.py
```

## Deploying as an Aiven Application

1. Set an environment variable named `MARIMO_TOKEN_PASSWORD` on the
   Application (Aiven Console → your project → your Application →
   environment variables) to whatever password you want to gate this
   notebook behind. The container refuses to start if it's unset --
   see the `Dockerfile` -- rather than silently deploying unprotected.
2. Point the deploy's build path at this directory, e.g. `build_path:
   examples/shared-server`, port `8080`.
3. Share the resulting URL with `?access_token=<your password>`
   appended, or let visitors hit the plain URL and enter the password
   at marimo's own login page.

No database or other service integration needed.

## Files

- `notebook.py` — the shared notebook. Nothing about it is
  WASM-specific or persistence-specific; the sharing and saving both
  come from running it as a real server rather than exporting it.
- `Dockerfile` — a single stage: install `marimo`, copy the notebook,
  run `marimo edit` bound to `0.0.0.0:8080` with the password from
  `MARIMO_TOKEN_PASSWORD`.
- `requirements.txt` — just `marimo`.
