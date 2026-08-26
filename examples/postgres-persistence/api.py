"""Tiny internal API bridging the WASM notebook to Postgres.

Pyodide (the Python-in-WASM runtime the notebook exports to) can only
speak HTTP -- it has no raw TCP sockets, so it can't open a psycopg
connection itself. This process is the one thing in the container that
actually touches the database; nginx reverse-proxies /api/* to it and
it binds to localhost only, so it's never reachable directly from the
outside.

Deliberately dependency-light (stdlib http.server, no framework): this
is a two-endpoint bridge, not a general-purpose API.
"""

import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import psycopg
from psycopg.types.json import Jsonb

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

DATABASE_URL = os.environ["DATABASE_URL"]

# Session ids are notebook-generated UUIDs (see notebook.py); keep the
# accepted shape narrow regardless.
PATH_RE = re.compile(r"^/api/(state|history)/([A-Za-z0-9_-]{1,128})$")


def get_connection():
    return psycopg.connect(DATABASE_URL)


def ensure_schema():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS state_history (
                    id BIGSERIAL PRIMARY KEY,
                    key TEXT NOT NULL,
                    value JSONB NOT NULL,
                    changed_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS state_history_key_changed_at_idx
                    ON state_history (key, changed_at DESC)
                """
            )
        conn.commit()


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        match = PATH_RE.match(urlparse(self.path).path)
        if not match:
            self._send_json(404, {"error": "not found"})
            return
        kind, key = match.groups()
        try:
            if kind == "state":
                with get_connection() as conn, conn.cursor() as cur:
                    cur.execute("SELECT value FROM app_state WHERE key = %s", (key,))
                    row = cur.fetchone()
                self._send_json(200, {"value": row[0] if row else None})
            else:
                with get_connection() as conn, conn.cursor() as cur:
                    cur.execute(
                        "SELECT changed_at, value FROM state_history "
                        "WHERE key = %s ORDER BY changed_at DESC LIMIT 20",
                        (key,),
                    )
                    rows = cur.fetchall()
                self._send_json(
                    200,
                    {
                        "history": [
                            {"changed_at": str(changed_at), **value}
                            for changed_at, value in rows
                        ]
                    },
                )
        except Exception as exc:  # noqa: BLE001 -- surface as JSON, not a stack trace
            self._send_json(500, {"error": str(exc)})

    def do_POST(self):
        match = PATH_RE.match(urlparse(self.path).path)
        if not match or match.group(1) != "state":
            self._send_json(404, {"error": "not found"})
            return
        _, key = match.groups()
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid json"})
            return
        value = payload.get("value")
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO app_state (key, value, updated_at)
                        VALUES (%s, %s, now())
                        ON CONFLICT (key)
                        DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                        """,
                        (key, Jsonb(value)),
                    )
                    cur.execute(
                        "INSERT INTO state_history (key, value) VALUES (%s, %s)",
                        (key, Jsonb(value)),
                    )
                conn.commit()
            self._send_json(200, {"ok": True})
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"error": str(exc)})

    def log_message(self, format, *args):  # noqa: A002 -- match base signature
        pass  # nginx's access log already covers request visibility


if __name__ == "__main__":
    ensure_schema()
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    server.serve_forever()
