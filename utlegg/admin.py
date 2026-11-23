import csv
import io

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from .db import execute, query
from .decorators import role_required

bp = Blueprint("admin", __name__, url_prefix="/admin")

ROLES = ["employee", "manager", "admin"]


@bp.route("/users")
@role_required("admin")
def users():
    all_users = query("SELECT id, email, full_name, department, role, created_at FROM users ORDER BY id")
    return render_template("admin/users.html", users=all_users, roles=ROLES)


@bp.route("/users", methods=["POST"])
@role_required("admin")
def create_user():
    f = request.form
    if not f.get("email") or not f.get("password") or not f.get("full_name"):
        flash("Name, email and password are required.", "error")
        return redirect(url_for("admin.users"))
    if f.get("role") not in ROLES:
        flash("Invalid role.", "error")
        return redirect(url_for("admin.users"))
    if query("SELECT 1 FROM users WHERE email = %s", (f["email"].lower(),), one=True):
        flash("A user with that email already exists.", "error")
        return redirect(url_for("admin.users"))
    execute(
        "INSERT INTO users (email, password_hash, full_name, department, role) VALUES (%s, %s, %s, %s, %s)",
        (f["email"].strip().lower(), generate_password_hash(f["password"]), f["full_name"],
         f.get("department") or "General", f["role"]),
    )
    flash(f"User {f['email']} created.", "success")
    return redirect(url_for("admin.users"))


@bp.route("/export.csv")
@role_required("admin")
def export_csv():
    """Monthly export for the accounting team (opened in Excel)."""
    rows = query(
        "SELECT e.id, u.full_name, u.department, u.bank_account, e.title, e.description, "
        "e.category, e.amount, e.currency, e.expense_date, e.status "
        "FROM expenses e JOIN users u ON u.id = e.user_id ORDER BY e.expense_date"
    )
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["ID", "Employee", "Department", "Bank account", "Title", "Description",
                     "Category", "Amount", "Currency", "Date", "Status"])
    for r in rows:
        writer.writerow([r["id"], r["full_name"], r["department"], r["bank_account"], r["title"],
                         r["description"] or "", r["category"], r["amount"], r["currency"],
                         r["expense_date"], r["status"]])
    return Response(
        buf.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=expenses.csv"},
    )
