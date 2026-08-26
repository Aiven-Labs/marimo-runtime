FROM python:3.11-slim AS export

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# uv is a build-time-only tool marimo needs to resolve dependencies for
# the html-wasm export below -- not needed at runtime.
RUN pip install --no-cache-dir uv

COPY notebook.py session_state.py export_notebooks.py .

# Same per-visitor WASM export as the root template: no shared server-side
# kernel ever runs a notebook's Python, so nothing here can execute
# arbitrary code against the database. Only api.py (below) touches Postgres.
#
# export_notebooks.py exports every *.py notebook sitting in this
# directory (just notebook.py by default) -- drop in more notebook files
# and they're picked up automatically, each getting its own WASM build
# plus a plain links page to move between them. All of them share this
# same api.py bridge and Postgres service (state is keyed by a random
# per-browser id, not by notebook), so no extra wiring is needed per
# notebook.
RUN python export_notebooks.py

# Runtime stage needs both nginx (serving the static WASM site) and Python
# (running the small state API) in one image, so this stays on
# Debian/glibc (python:3.11-slim) rather than nginx:alpine -- psycopg's
# prebuilt wheels target glibc, not musl.
FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default

RUN pip install --no-cache-dir "psycopg[binary]>=3.1"

COPY --from=export /site /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY api.py start.sh /app/
RUN chmod +x /app/start.sh

# Aiven Applications injects DATABASE_URL as an environment variable at
# runtime when a Postgres service integration is attached -- nothing
# secret is baked into this image.
EXPOSE 8080

CMD ["/app/start.sh"]
