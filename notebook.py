import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium", app_title="marimo on Aiven Runtimes")


@app.cell
def __():
    import marimo as mo
    return (mo,)


@app.cell
def __(mo):
    mo.md(
        """
        # 👋 Welcome to your marimo notebook

        This is a placeholder. It's here to prove the round trip works:
        **fork this repo → deploy it → get an interactive notebook running
        in the cloud** on Aiven Runtimes.

        Delete these cells and write your own notebook, or drop in an
        existing one (see the README for converting a Jupyter `.ipynb`).
        The slider below is just here to show that marimo's reactivity —
        cells rerunning automatically when their inputs change — works
        out of the box once deployed.
        """
    )
    return


@app.cell
def __(mo):
    n = mo.ui.slider(1, 10, value=3, label="Pick a number")
    n
    return (n,)


@app.cell
def __(mo, n):
    mo.md(f"{n.value} squared is **{n.value ** 2}**.")
    return


if __name__ == "__main__":
    app.run()
