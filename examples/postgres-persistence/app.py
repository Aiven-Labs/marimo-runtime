import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium", app_title="marimo + Aiven for PostgreSQL")


@app.cell
def __():
    import marimo as mo
    import os
    import json
    from datetime import datetime, timezone

    import psycopg
    from psycopg.types.json import Jsonb
    from dotenv import load_dotenv

    load_dotenv()
    return Jsonb, datetime, json, mo, os, psycopg, timezone


@app.cell
def __(mo):
    mo.md(
        """
        # marimo, backed by Aiven for PostgreSQL

        Every widget below stores its value in a real Postgres database
        (an Aiven for PostgreSQL service) instead of only living in this
        notebook's memory. Change a widget, then restart this notebook
        (`Ctrl+C` and re-run, or reload the page) — the values come back
        exactly where you left them, and the history table at the bottom
        shows every change was durably written to Postgres, not just kept
        in this Python process.
        """
    )
    return


@app.cell
def __(os):
    # When deployed as an Aiven Application with a PostgreSQL service
    # integration attached, Aiven injects a ready-to-use connection string
    # as DATABASE_URL. Locally (via .env) we fall back to individual
    # PG* vars. Aiven services always require TLS.
    _database_url = os.environ.get("DATABASE_URL")
    if _database_url:
        CONNINFO = _database_url
    else:
        CONNINFO = (
            f"host={os.environ['PGHOST']} "
            f"port={os.environ.get('PGPORT', '5432')} "
            f"dbname={os.environ.get('PGDATABASE', 'defaultdb')} "
            f"user={os.environ['PGUSER']} "
            f"password={os.environ['PGPASSWORD']} "
            f"sslmode={os.environ.get('PGSSLMODE', 'require')}"
        )
    return (CONNINFO,)


@app.cell
def __(CONNINFO, psycopg):
    def get_connection():
        return psycopg.connect(CONNINFO)

    # Make sure the tables exist. Safe to run on every notebook start.
    with get_connection() as _conn:
        with _conn.cursor() as _cur:
            _cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            _cur.execute(
                """
                CREATE TABLE IF NOT EXISTS state_history (
                    id BIGSERIAL PRIMARY KEY,
                    key TEXT NOT NULL,
                    value JSONB NOT NULL,
                    changed_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        _conn.commit()
    return (get_connection,)


@app.cell
def __(Jsonb, get_connection):
    def load_state(key: str, default: dict) -> dict:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT value FROM app_state WHERE key = %s", (key,))
                row = cur.fetchone()
                return row[0] if row else default

    def save_state(key: str, value: dict) -> None:
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

    return load_state, save_state


@app.cell
def __(load_state):
    # The one and only load from Postgres at notebook startup.
    _saved = load_state(
        "widgets",
        default={
            "favorite_number": 5,
            "favorite_color": "Teal",
            "visitor_name": "",
            "subscribe_updates": False,
        },
    )
    return (_saved,)


@app.cell
def __(_saved, mo):
    favorite_number = mo.ui.slider(
        start=0, stop=100, value=_saved["favorite_number"], label="Favorite number"
    )
    favorite_color = mo.ui.dropdown(
        options=["Teal", "Coral", "Slate", "Amber", "Violet"],
        value=_saved["favorite_color"],
        label="Favorite color",
    )
    visitor_name = mo.ui.text(value=_saved["visitor_name"], label="Your name")
    subscribe_updates = mo.ui.checkbox(
        value=_saved["subscribe_updates"], label="Subscribe to updates"
    )

    mo.hstack([favorite_number, favorite_color, visitor_name, subscribe_updates])
    return favorite_color, favorite_number, subscribe_updates, visitor_name


@app.cell
def __(
    datetime,
    favorite_color,
    favorite_number,
    mo,
    save_state,
    subscribe_updates,
    timezone,
    visitor_name,
):
    # This cell reruns automatically whenever any widget above changes
    # (marimo's reactive execution), and writes the new value straight
    # to Postgres — both the current-state table and the history log.
    current_value = {
        "favorite_number": favorite_number.value,
        "favorite_color": favorite_color.value,
        "visitor_name": visitor_name.value,
        "subscribe_updates": subscribe_updates.value,
    }
    save_state("widgets", current_value)
    last_saved_at = datetime.now(timezone.utc).isoformat()

    mo.md(f"Saved to Postgres at `{last_saved_at}`: `{current_value}`")
    return current_value, last_saved_at


@app.cell
def __(get_connection, last_saved_at, mo):
    # Depends on last_saved_at purely so this cell re-runs after each
    # save above and shows the freshest history straight from the DB.
    with get_connection() as _conn:
        with _conn.cursor() as _cur:
            _cur.execute(
                """
                SELECT changed_at, value
                FROM state_history
                WHERE key = 'widgets'
                ORDER BY changed_at DESC
                LIMIT 20
                """
            )
            _rows = _cur.fetchall()

    history_rows = [
        {"changed_at": str(changed_at), **value} for changed_at, value in _rows
    ]

    mo.vstack(
        [
            mo.md(f"_(last refreshed using write at `{last_saved_at}`)_"),
            mo.md("### Change history, read back from `state_history` in Postgres"),
            mo.ui.table(history_rows, selection=None),
        ]
    )
    return (history_rows,)


@app.cell
def __(CONNINFO, mo, os):
    if CONNINFO.startswith("postgres"):
        from urllib.parse import urlparse

        _host = urlparse(CONNINFO).hostname or "(unknown)"
    else:
        _host = os.environ.get("PGHOST", "(unset)")

    mo.md(
        f"""
        ---
        Connected to `{_host}` — an Aiven for PostgreSQL service. Widget
        state and history live entirely in that database, not in this
        notebook process.
        """
    )
    return


if __name__ == "__main__":
    app.run()
