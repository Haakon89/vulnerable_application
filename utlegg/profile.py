from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import execute, query
from .decorators import login_required

bp = Blueprint("profile", __name__)

# Fields we never want to touch through the generic update
PROTECTED_FIELDS = {"id", "password_hash", "created_at"}


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = query("SELECT * FROM users WHERE id = %s", (session["user_id"],), one=True)

    if request.method == "POST":
        editable = [c for c in user.keys() if c not in PROTECTED_FIELDS]
        updates = {k: v for k, v in request.form.items() if k in editable}
        if updates:
            assignments = ", ".join(f"{col} = %s" for col in updates)
            execute(
                f"UPDATE users SET {assignments} WHERE id = %s",
                (*updates.values(), session["user_id"]),
            )
            if "full_name" in updates:
                session["name"] = updates["full_name"]
            flash("Profile updated.", "success")
        return redirect(url_for("profile.profile"))

    return render_template("profile.html", user=user)


@bp.route("/profile/password", methods=["POST"])
@login_required
def change_password():
    user = query("SELECT password_hash FROM users WHERE id = %s", (session["user_id"],), one=True)
    if not check_password_hash(user["password_hash"], request.form.get("current", "")):
        flash("Current password is incorrect.", "error")
    elif request.form.get("new") != request.form.get("confirm"):
        flash("New passwords do not match.", "error")
    elif len(request.form.get("new", "")) < 8:
        flash("New password must be at least 8 characters.", "error")
    else:
        execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (generate_password_hash(request.form["new"]), session["user_id"]),
        )
        flash("Password changed.", "success")
    return redirect(url_for("profile.profile"))
