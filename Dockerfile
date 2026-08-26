FROM python:3.11-slim AS export

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

# Serve with nginx instead of Python's http.server: the exported bundle
# is tens of MB of mostly-text assets (the editor UI plus the Pyodide
# runtime), and http.server never compresses anything, which makes
# first load painfully slow. nginx gzips on the fly and long-caches the
# content-hashed asset files.
FROM nginx:alpine

COPY --from=export /site /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
