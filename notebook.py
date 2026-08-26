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

        This is a placeholder! 
        
        Delete these cells and write your own notebook, or drop in an
        existing one (see the README for converting a Jupyter `.ipynb`).
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


@app.cell
def __(mo):
    mo.md(
        """
        ---
        *This is your own private, editable copy of this notebook!* Nothing you change here
        affects anyone else. Get the template that made it:
        [github.com/Aiven-Labs/marimo-runtime](https://github.com/Aiven-Labs/marimo-runtime).
        """
    )
    return


if __name__ == "__main__":
    app.run()
