import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium", app_title="marimo + Aiven for PostgreSQL")


@app.cell(hide_code=True)
def __():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
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
def __():
    # session_state.py lives next to this notebook, not inside it -- see
    # that file for the session id and the Postgres load/save/history
    # calls it wraps. marimo's WASM export bundles it automatically.
    from session_state import get_or_create_session_id, notebook_key

    session_id = get_or_create_session_id()
    # This directory has more than one notebook persisting state under
    # the same session id -- see temperature_converter.py -- so each
    # needs its own namespace to avoid overwriting the other's saved data.
    state_key = notebook_key(session_id, "favorites")
    return session_id, state_key


@app.cell(hide_code=True)
async def __(state_key):
    from session_state import load_state

    _default = {
        "favorite_number": 5,
        "favorite_color": "Teal",
        "visitor_name": "",
        "subscribe_updates": False,
    }
    # The one and only load from Postgres, at notebook startup.
    saved_state = await load_state(state_key, _default)
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
    favorite_color,
    favorite_number,
    mo,
    state_key,
    subscribe_updates,
    visitor_name,
):
    from session_state import save_state

    # Reruns automatically whenever a widget above changes (marimo's
    # reactive execution), and persists the new value through
    # session_state rather than talking to Postgres directly.
    current_value = {
        "favorite_number": favorite_number.value,
        "favorite_color": favorite_color.value,
        "visitor_name": visitor_name.value,
        "subscribe_updates": subscribe_updates.value,
    }
    save_status = await save_state(state_key, current_value)

    mo.md(f"**{save_status}**: `{current_value}`")
    return current_value, save_status


@app.cell(hide_code=True)
async def __(mo, save_status, state_key):
    from session_state import load_history

    # Depends on save_status purely so this cell reruns after each save
    # above and shows the freshest history straight from the database.
    history_rows = await load_history(state_key)

    mo.vstack(
        [
            mo.md("### Your change history, read back from Postgres"),
            mo.ui.table(history_rows, selection=None)
            if history_rows
            else mo.md("_(no history yet -- change a widget above)_"),
        ]
    )
    return (history_rows,)


@app.cell(hide_code=True)
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
