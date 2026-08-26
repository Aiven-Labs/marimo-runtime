import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium", app_title="Temperature Converter")


@app.cell(hide_code=True)
def __():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def __(mo):
    mo.md(
        """
        # 🌡️ Temperature converter, persisted

        The same [Temperature Converter](../../temperature_converter.py)
        notebook as the root template's second example, but wired up to
        `session_state.py`: your last Celsius value survives a reload.
        `notebook.py` in this same directory is the fuller persistence
        example (four widgets, a change history); this one is
        deliberately minimal, to show the same load/save pattern with as
        little else going on as possible.
        """
    )
    return


@app.cell(hide_code=True)
def __():
    # See notebook.py's first cell for why this needs its own namespace,
    # not just the bare session id.
    from session_state import get_or_create_session_id, notebook_key

    session_id = get_or_create_session_id()
    state_key = notebook_key(session_id, "temperature")
    return session_id, state_key


@app.cell(hide_code=True)
async def __(state_key):
    from session_state import load_state

    # The one and only load from Postgres, at notebook startup.
    saved_state = await load_state(state_key, {"celsius": 20})
    return (saved_state,)


@app.cell
def __(mo, saved_state):
    celsius = mo.ui.slider(-40, 100, value=saved_state["celsius"], label="Celsius")
    celsius
    return (celsius,)


@app.cell(hide_code=True)
async def __(celsius, state_key):
    from session_state import save_state

    # Reruns automatically whenever the slider above changes (marimo's
    # reactive execution), and persists the new value through
    # session_state rather than talking to Postgres directly.
    save_status = await save_state(state_key, {"celsius": celsius.value})
    return (save_status,)


@app.cell
def __(celsius, mo, save_status):
    fahrenheit = celsius.value * 9 / 5 + 32
    mo.md(
        f"**{celsius.value}°C** is **{fahrenheit:.1f}°F**. {save_status} -- "
        "reload this page in the same browser and it comes back."
    )
    return (fahrenheit,)


@app.cell(hide_code=True)
def __(mo):
    mo.md(
        """
        ---
        Get the template that made this:
        [github.com/Aiven-Labs/marimo-runtime](https://github.com/Aiven-Labs/marimo-runtime).
        """
    )
    return


if __name__ == "__main__":
    app.run()
