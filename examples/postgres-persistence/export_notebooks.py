#!/usr/bin/env python3
"""Export every marimo notebook in this directory to its own WASM build.

Run at Docker build time (see Dockerfile) instead of a single hardcoded
`marimo export html-wasm notebook.py`. Notebooks are discovered by
scanning the *.py files sitting next to this script for a `marimo.App(`
call, so dropping in another notebook file is enough to get it built and
linked -- no Dockerfile edit needed.

marimo has no built-in way to navigate between separate WASM exports
(each is a fully self-contained Pyodide bundle with no shared runtime or
file browser -- that's a server-only feature). So: with exactly one
notebook, export it straight to the site root, preserving the original
single-notebook behaviour exactly. With more than one, each gets its own
subdirectory and a plain, static index.html links to all of them --
that's the smallest thing that works, and it's the same pattern marimo's
own multi-notebook deployment guide recommends.
"""

import pathlib
import re
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
APP_RE = re.compile(r"marimo\.App\(")


def discover_notebooks() -> list[pathlib.Path]:
    notebooks = []
    for path in sorted(HERE.glob("*.py")):
        if path.name == pathlib.Path(__file__).name:
            continue
        if APP_RE.search(path.read_text()):
            notebooks.append(path)
    return notebooks


def slug_for(path: pathlib.Path) -> str:
    return path.stem.replace("_", "-")


def title_for(path: pathlib.Path) -> str:
    return path.stem.replace("_", " ").replace("-", " ").title()


def export_one(path: pathlib.Path, out_dir: pathlib.Path) -> None:
    # `-m marimo` rather than relying on a `marimo` console script being on
    # PATH -- more robust across base images/environments.
    subprocess.run(
        [
            sys.executable,
            "-m",
            "marimo",
            "export",
            "html-wasm",
            str(path),
            "-o",
            str(out_dir),
            "--mode",
            "edit",
            "-f",
        ],
        check=True,
    )


def copy_wheels_to_root(notebook_dir: pathlib.Path, site: pathlib.Path) -> None:
    """Copy this notebook's local-module wheels up to the site root too.

    marimo bundles a notebook-local import (like session_state.py) into a
    wheel and references it with a relative URL that gets resolved in the
    browser, not baked in at build time. In this nested multi-notebook
    layout that relative reference has been observed to resolve one
    directory level higher than intended -- landing on the site root
    instead of this notebook's own subdirectory. Having the wheel exist
    at both places means that wrong resolution still finds the real file
    instead of 404ing -- see nginx.conf's /public/ location for the other
    half of this belt-and-suspenders fix.
    """
    wheels_dir = notebook_dir / "public" / "wheels"
    if not wheels_dir.is_dir():
        return
    root_wheels_dir = site / "public" / "wheels"
    root_wheels_dir.mkdir(parents=True, exist_ok=True)
    for wheel in wheels_dir.glob("*.whl"):
        shutil.copy2(wheel, root_wheels_dir / wheel.name)


def write_index(notebooks: list[pathlib.Path], site: pathlib.Path) -> None:
    items = "\n".join(
        f'      <li><a href="./{slug_for(nb)}/">{title_for(nb)}</a></li>'
        for nb in notebooks
    )
    site.mkdir(parents=True, exist_ok=True)
    (site / "index.html").write_text(
        f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Notebooks</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      body {{
        font-family: system-ui, sans-serif;
        max-width: 40rem;
        margin: 4rem auto;
        padding: 0 1rem;
        color: #1a1a1a;
      }}
      li {{ margin: 0.6rem 0; font-size: 1.15rem; }}
      a {{ color: #0b6e4f; text-decoration: none; }}
      a:hover {{ text-decoration: underline; }}
    </style>
  </head>
  <body>
    <h1>Notebooks</h1>
    <ul>
{items}
    </ul>
  </body>
</html>
"""
    )


def main() -> None:
    site = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("/site")

    notebooks = discover_notebooks()
    if not notebooks:
        sys.exit(
            "No marimo notebooks found next to export_notebooks.py "
            "(no *.py file defines marimo.App(...))."
        )

    if len(notebooks) == 1:
        # Single notebook: export straight to the site root, same as the
        # original hardcoded `marimo export html-wasm notebook.py -o /site`.
        export_one(notebooks[0], site)
        return

    for notebook in notebooks:
        out_dir = site / slug_for(notebook)
        export_one(notebook, out_dir)
        copy_wheels_to_root(out_dir, site)
    write_index(notebooks, site)


if __name__ == "__main__":
    main()
