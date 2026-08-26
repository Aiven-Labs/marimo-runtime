import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium", app_title="Shared marimo notebook")


@app.cell
def __():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def __(mo):
    mo.md(
        """
        # A shared, editable notebook

        Unlike the root template's WASM export, this notebook runs as a
        real marimo server: one live Python kernel, shared by everyone
        who has the password. Edit a cell below and save (`Ctrl+S`, or
        just wait for autosave) and the change lands in `notebook.py` on
        disk -- anyone else connected sees it too.

        That's also the trade-off: there's no per-visitor isolation
        here, and no sandbox. Anyone with the password can read, edit,
        and run arbitrary Python in this container -- see this example's
        README before pointing it at anything you care about.
        """
    )
    return


@app.cell
def __(mo):
    name = mo.ui.text(placeholder="Type your name", label="Who's editing?")
    name
    return (name,)


@app.cell
def __(mo, name):
    greeting = f"Hello, {name.value}!" if name.value else "Waiting for a name above..."
    mo.md(f"## {greeting}")
    return (greeting,)


@app.cell(hide_code=True)
def __(mo):
    mo.md(
        """
        ---
        Try it: open this page in two browser tabs. Type a name in one,
        then edit *this* cell's text in the other and save. Reload the
        first tab and your edit is there too -- it's the same file on
        the same server, not two private copies.

        Get the template that made this:
        [github.com/Aiven-Labs/marimo-runtime](https://github.com/Aiven-Labs/marimo-runtime).
        """
    )
    return


if __name__ == "__main__":
    app.run()
