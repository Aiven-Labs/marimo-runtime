import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium", app_title="Temperature Converter")


@app.cell
def __():
    import marimo as mo

    return (mo,)


@app.cell
def __(mo):
    mo.md(
        """
        # 🌡️ Temperature converter

        A second, unrelated notebook dropped into this same directory --
        `export_notebooks.py` picks it up automatically alongside
        `notebook.py` and links the two from a shared index page. See
        the README's [Multiple notebooks](README.md#multiple-notebooks)
        section for how that works.
        """
    )
    return


@app.cell
def __(mo):
    celsius = mo.ui.slider(-40, 100, value=20, label="Celsius")
    celsius
    return (celsius,)


@app.cell
def __(celsius, mo):
    fahrenheit = celsius.value * 9 / 5 + 32
    mo.md(f"**{celsius.value}°C** is **{fahrenheit:.1f}°F**.")
    return (fahrenheit,)


@app.cell
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
