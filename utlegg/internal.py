"""Health/status endpoint for the ops team. Only reachable from the server itself."""
import os

from flask import Blueprint, abort, current_app, jsonify, request

from .db import query

bp = Blueprint("internal", __name__, url_prefix="/internal")


@bp.route("/status")
def status():
    if request.remote_addr not in ("127.0.0.1", "::1"):
        abort(403)

    try:
        query("SELECT 1 AS ok")
        db_ok = True
    except Exception:
        db_ok = False

    return jsonify({
        "app": current_app.config["APP_NAME"],
        "version": current_app.config["APP_VERSION"],
        "debug": current_app.debug,
        "database": "ok" if db_ok else "error",
        "integrations": {k: v for k, v in os.environ.items() if k.startswith("UTLEGG_")},
    })
