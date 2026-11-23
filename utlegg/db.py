"""Small database helper so we can write plain SQL.

Postgres in Docker, SQLite for quick local runs (DATABASE_URL=sqlite:///utlegg.db).
"""
import os
import sqlite3

import click
from flask import current_app, g

try:
    import psycopg2
    import psycopg2.extras
except ImportError:  # SQLite-only environments
    psycopg2 = None


def _is_sqlite(url):
    return url.startswith("sqlite:///")


def get_db():
    if "db" not in g:
        url = current_app.config["DATABASE_URL"]
        if _is_sqlite(url):
            conn = sqlite3.connect(url[len("sqlite:///"):])
            conn.row_factory = sqlite3.Row
            g.db_kind = "sqlite"
        else:
            conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
            g.db_kind = "postgres"
        g.db = conn
    return g.db


def _adapt(sql):
    # Queries are written with %s placeholders (psycopg2 style)
    if g.get("db_kind") == "sqlite":
        return sql.replace("%s", "?")
    return sql


def query(sql, params=(), one=False):
    db = get_db()
    cur = db.cursor()
    cur.execute(_adapt(sql), params)
    rows = cur.fetchall() if cur.description else []
    rows = [dict(r) for r in rows]
    cur.close()
    return (rows[0] if rows else None) if one else rows


def execute(sql, params=(), returning=False):
    db = get_db()
    cur = db.cursor()
    cur.execute(_adapt(sql), params)
    result = None
    if returning:
        row = cur.fetchone()
        result = dict(row) if row else None
    db.commit()
    cur.close()
    return result


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(seed=True):
    get_db()
    with current_app.open_resource("schema.sql") as f:
        schema = f.read().decode()
    if g.db_kind == "sqlite":
        schema = schema.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
        g.db.executescript(schema)
    else:
        cur = g.db.cursor()
        cur.execute(schema)
        g.db.commit()
        cur.close()
    if seed:
        from .seed import seed_data
        seed_data()


def tables_exist():
    try:
        query("SELECT 1 FROM users LIMIT 1")
        return True
    except Exception:
        get_db().rollback()
        return False


@click.command("init-db")
@click.option("--reset", is_flag=True, help="Drop and recreate all tables.")
def init_db_command(reset):
    """Create tables and demo data (skips if they already exist)."""
    if tables_exist() and not reset:
        click.echo("Database already initialised.")
        return
    init_db()
    click.echo("Initialised the database with demo data.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
