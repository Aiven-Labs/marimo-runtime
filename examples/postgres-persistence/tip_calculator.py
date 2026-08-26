import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium", app_title="Tip Calculator")


@app.cell(hide_code=True)
def __():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def __(mo):
    mo.md(
        """
        # 🧾 Tip calculator

        A second, plain notebook dropped into this same directory --
        nothing here talks to Postgres or `session_state.py`. It's here
        to show that `export_notebooks.py` links together whatever
        notebooks it finds, whether or not they share the persistence
        backend sitting next to them.
        """
    )
    return


@app.cell
def __(mo):
    bill = mo.ui.number(start=0, stop=1000, value=42, label="Bill total ($)")
    tip_percent = mo.ui.slider(0, 30, value=18, label="Tip %")
    mo.hstack([bill, tip_percent])
    return bill, tip_percent


@app.cell
def __(bill, mo, tip_percent):
    tip = bill.value * tip_percent.value / 100
    mo.md(f"Tip: **${tip:.2f}** -- total: **${bill.value + tip:.2f}**")
    return (tip,)


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
