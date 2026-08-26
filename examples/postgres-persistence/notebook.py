import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium", app_title="marimo + Aiven for PostgreSQL")


@app.cell(hide_code=True)
def __():
    import marimo as mo
    import sys
    import os
    import json
    import uuid

    # Pyodide (the Python-in-WASM runtime this notebook exports to) reports
    # "emscripten" here; a normal `marimo edit` process reports the real OS.
    IN_BROWSER = sys.platform == "emscripten"
    return IN_BROWSER, json, mo, os, sys, uuid


@app.cell
def __(mo):
    mo.md(
        """
        # marimo, with your own private *and* saved state

        This notebook exports to WASM like the root template -- your
        browser runs its own private Pyodide (Python-in-WebAssembly)
        instance, so nobody else can see or touch your copy while you're
        editing it.

        The difference: every widget change is also sent to a tiny API
        bundled into this same container, which writes it to a real
        **Aiven for PostgreSQL** service, keyed by a random id stored in
        *your* browser. Reload the page (same browser) and your widgets
        come back exactly where you left them.
        """
    )
    return


@app.cell(hide_code=True)
def __(IN_BROWSER, os, uuid):
    if IN_BROWSER:
        import js

        session_id = js.window.localStorage.getItem("marimo_session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            js.window.localStorage.setItem("marimo_session_id", session_id)
    else:
        # Local (non-WASM) preview has no browser localStorage to persist
        # to -- reuse a fixed id across runs instead.
        session_id = os.environ.get("MARIMO_LOCAL_SESSION_ID", "local-preview")
    return (session_id,)


@app.cell(hide_code=True)
def __(IN_BROWSER, json):
    # Pyodide can't open a raw TCP socket, so the notebook never talks to
    # Postgres directly -- it calls this same container's bundled API over
    # plain HTTP (relative paths, so it works at whatever domain this is
    # deployed to). Locally, outside Pyodide, fall back to urllib against
    # that same API running on 127.0.0.1:8000.
    async def api_get(path: str):
        if IN_BROWSER:
            import pyodide.http

            response = await pyodide.http.pyfetch(path)
            return await response.json()
        else:
            import urllib.request

            with urllib.request.urlopen("http://127.0.0.1:8000" + path) as resp:
                return json.load(resp)

    async def api_post(path: str, payload: dict):
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
        else:
            import urllib.request

            req = urllib.request.Request(
                "http://127.0.0.1:8000" + path,
                data=body.encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req) as resp:
                return json.load(resp)

    return api_get, api_post


@app.cell(hide_code=True)
async def __(api_get, session_id):
    # The one and only load from Postgres, at notebook startup.
    _default = {
        "favorite_number": 5,
        "favorite_color": "Teal",
        "visitor_name": "",
        "subscribe_updates": False,
    }
    try:
        _response = await api_get(f"/api/state/{session_id}")
        saved_state = _response.get("value") or _default
    except Exception:
        # API not reachable (e.g. this local preview isn't running api.py
        # too) -- fall back to defaults so the notebook still works.
        saved_state = _default
    return (saved_state,)


@app.cell
def __(mo, saved_state):
    favorite_number = mo.ui.slider(
        start=0, stop=100, value=saved_state["favorite_number"], label="Favorite number"
    )
    favorite_color = mo.ui.dropdown(
        options=["Teal", "Coral", "Slate", "Amber", "Violet"],
        value=saved_state["favorite_color"],
        label="Favorite color",
    )
    visitor_name = mo.ui.text(value=saved_state["visitor_name"], label="Your name")
    subscribe_updates = mo.ui.checkbox(
        value=saved_state["subscribe_updates"], label="Subscribe to updates"
    )

    mo.hstack([favorite_number, favorite_color, visitor_name, subscribe_updates])
    return favorite_color, favorite_number, subscribe_updates, visitor_name


@app.cell(hide_code=True)
async def __(
    api_post,
    favorite_color,
    favorite_number,
    mo,
    session_id,
    subscribe_updates,
    visitor_name,
):
    # Reruns automatically whenever a widget above changes (marimo's
    # reactive execution), and persists the new value through the bundled
    # API rather than talking to Postgres directly.
    current_value = {
        "favorite_number": favorite_number.value,
        "favorite_color": favorite_color.value,
        "visitor_name": visitor_name.value,
        "subscribe_updates": subscribe_updates.value,
    }
    try:
        await api_post(f"/api/state/{session_id}", {"value": current_value})
        save_status = "Saved to Postgres"
    except Exception as _exc:
        save_status = f"Not saved -- API unreachable ({_exc})"

    mo.md(f"**{save_status}**: `{current_value}`")
    return current_value, save_status


@app.cell(hide_code=True)
async def __(api_get, mo, save_status, session_id):
    # Depends on save_status purely so this cell reruns after each save
    # above and shows the freshest history straight from the database.
    try:
        _response = await api_get(f"/api/history/{session_id}")
        history_rows = _response.get("history", [])
    except Exception:
        history_rows = []

    mo.vstack(
        [
            mo.md("### Your change history, read back from Postgres"),
            mo.ui.table(history_rows, selection=None)
            if history_rows
            else mo.md("_(no history yet -- change a widget above)_"),
        ]
    )
    return (history_rows,)


@app.cell
def __(mo, session_id):
    mo.md(
        f"""
        ---
        You're identified as `{session_id[:8]}…`, a random id generated
        on your first visit and stored in *this browser's* `localStorage` --
        no login involved. Reload this page in the same browser and it
        comes back; open it in a different browser or an incognito window
        and you'll get a brand-new, empty session.

        Get the template that made this:
        [github.com/Aiven-Labs/marimo-runtime](https://github.com/Aiven-Labs/marimo-runtime).
        """
    )
    return


if __name__ == "__main__":
    app.run()
