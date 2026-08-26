FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# uv is a build-time-only tool marimo needs to resolve dependencies for
# the html-wasm export below -- not needed at runtime.
RUN pip install --no-cache-dir uv

COPY notebook.py .

# Export to a self-contained WASM build at image-build time, not at
# container start. Each visitor's browser then runs its own private
# Pyodide (Python-in-WASM) instance -- there's no shared server-side
# kernel, so every visitor gets their own independent, editable copy
# of the notebook with no risk of visitors overwriting each other's
# edits, and no arbitrary code ever executes on this container.
RUN marimo export html-wasm notebook.py -o /site --mode edit -f

EXPOSE 8080

CMD ["python", "-m", "http.server", "8080", "--directory", "/site"]
