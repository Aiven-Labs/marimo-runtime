"""Session identity and the Postgres-backed state bridge for the notebook.

Kept out of notebook.py entirely -- not just hidden -- so the notebook
file itself only contains the widgets and narrative, not the mechanism
that identifies "you" (a random id stored in your browser) and moves
your saved state to/from Postgres through the bundled api.py.

Pyodide can't open a raw database connection, so every call here goes
over plain HTTP to that same-origin API instead. marimo's WASM export
bundles local imports like this one automatically -- it resolves this
file into a wheel and embeds it as a dependency at export time (see
`marimo export html-wasm`'s notebook-local module resolution) -- so
notebook.py can just `import session_state` with no extra config.
"""

import json
import os
import sys
import uuid

IN_BROWSER = sys.platform == "emscripten"


def get_or_create_session_id() -> str:
    """A random id identifying *this browser*, no login involved."""
    if IN_BROWSER:
        import js

        session_id = js.window.localStorage.getItem("marimo_session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            js.window.localStorage.setItem("marimo_session_id", session_id)
        return session_id
    # Local (non-WASM) preview has no browser localStorage to persist to --
    # reuse a fixed id across runs instead.
    return os.environ.get("MARIMO_LOCAL_SESSION_ID", "local-preview")


def notebook_key(session_id: str, namespace: str) -> str:
    """A storage key unique to both this browser *and* this notebook.

    `session_id` identifies the browser, not any one notebook -- if more
    than one notebook in this directory persists state, they all share
    that same session id. Without a per-notebook `namespace`, two
    notebooks calling `load_state`/`save_state` with the bare session id
    would read and overwrite each other's data in `app_state`, since
    api.py only keys on whatever string it's given. Give each notebook
    that persists state its own namespace (e.g. "favorites",
    "temperature") to keep them apart.
    """
    return f"{session_id}:{namespace}"


async def _api_get(path: str):
    if IN_BROWSER:
        import pyodide.http

        response = await pyodide.http.pyfetch(path)
        return await response.json()
    import urllib.request

    with urllib.request.urlopen("http://127.0.0.1:8000" + path) as resp:
        return json.load(resp)


async def _api_post(path: str, payload: dict):
    body = json.dumps(payload)
    if IN_BROWSER:
        import pyodide.http

        response = await pyodide.http.pyfetch(
            path,
            method="POST",
            headers={"Content-Type": "application/json"},
            body=body,
        )
        return await response.json()
    import urllib.request

    req = urllib.request.Request(
        "http://127.0.0.1:8000" + path,
        data=body.encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


async def load_state(key: str, default: dict) -> dict:
    """The one and only load from Postgres, meant to run at notebook startup.

    `key` is whatever string identifies this notebook's state to api.py --
    use `notebook_key(session_id, namespace)`, not the bare session id, if
    more than one notebook persists state (see `notebook_key`).
    """
    try:
        response = await _api_get(f"/api/state/{key}")
        return response.get("value") or default
    except Exception:
        # API not reachable (e.g. this local preview isn't running api.py
        # too) -- fall back to defaults so the notebook still works.
        return default


async def save_state(key: str, value: dict) -> str:
    """Persist `value` under `key`; returns a human-readable status."""
    try:
        await _api_post(f"/api/state/{key}", {"value": value})
        return "Saved to Postgres"
    except Exception as exc:
        return f"Not saved -- API unreachable ({exc})"


async def load_history(key: str) -> list:
    """Most recent saved values under `key`, newest first."""
    try:
        response = await _api_get(f"/api/history/{key}")
        return response.get("history", [])
    except Exception:
        return []
