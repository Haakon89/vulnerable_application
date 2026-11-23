import os
import time
from datetime import datetime
from urllib.parse import urlparse

import requests
from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, send_from_directory, session,
                   url_for)

from .db import execute, query
from .decorators import login_required, role_required

bp = Blueprint("expenses", __name__)

CATEGORIES = ["Travel", "Accommodation", "Meals", "Equipment", "Software", "Training", "Other"]


def allowed_file(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]


@bp.route("/expenses")
@login_required
def list_expenses():
    search = request.args.get("q", "")
    sort = request.args.get("sort", "expense_date")
    order = request.args.get("order", "desc")
    if order.lower() not in ("asc", "desc"):
        order = "desc"

    # Column names can't be passed as query parameters, so the ORDER BY is built here
    sql = (
        "SELECT id, title, category, amount, currency, expense_date, status "
        "FROM expenses WHERE user_id = %s AND LOWER(title) LIKE LOWER(%s) "
        f"ORDER BY {sort} {order}"
    )
    expenses = query(sql, (session["user_id"], f"%{search}%"))
    total_pending = sum(float(e["amount"]) for e in expenses if e["status"] == "pending")
    return render_template(
        "expenses/list.html", expenses=expenses, search=search, sort=sort,
        order=order, total_pending=total_pending,
    )


@bp.route("/expenses/new", methods=["GET", "POST"])
@login_required
def new_expense():
    if request.method == "POST":
        form = request.form
        try:
            amount = round(float(form.get("amount", "0").replace(",", ".")), 2)
            expense_date = datetime.strptime(form.get("expense_date", ""), "%Y-%m-%d").date()
        except ValueError:
            flash("Please enter a valid amount and date.", "error")
            return render_template("expenses/new.html", categories=CATEGORIES, form=form)

        if amount <= 0 or not form.get("title"):
            flash("Title and a positive amount are required.", "error")
            return render_template("expenses/new.html", categories=CATEGORIES, form=form)

        receipt_filename = None
        receipt = request.files.get("receipt")
        receipt_url = form.get("receipt_url", "").strip()

        if receipt and receipt.filename:
            if not allowed_file(receipt.filename):
                flash("Receipts must be an image or PDF.", "error")
                return render_template("expenses/new.html", categories=CATEGORIES, form=form)
            receipt_filename = receipt.filename
            receipt.save(os.path.join(current_app.config["UPLOAD_FOLDER"], receipt_filename))
        elif receipt_url:
            # Lets people import receipts straight from the supplier's web portal
            try:
                resp = requests.get(receipt_url, timeout=5)
                resp.raise_for_status()
            except requests.RequestException as exc:
                flash(f"Could not download receipt: {exc}", "error")
                return render_template("expenses/new.html", categories=CATEGORIES, form=form)
            name = os.path.basename(urlparse(receipt_url).path) or "receipt"
            receipt_filename = f"imported_{int(time.time())}_{name}"
            with open(os.path.join(current_app.config["UPLOAD_FOLDER"], receipt_filename), "wb") as f:
                f.write(resp.content)

        row = execute(
            "INSERT INTO expenses (user_id, title, description, category, amount, currency, expense_date, receipt_filename) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (session["user_id"], form["title"], form.get("description"), form.get("category", "Other"),
             amount, form.get("currency", "NOK"), expense_date, receipt_filename),
            returning=True,
        )
        flash("Expense claim submitted.", "success")
        return redirect(url_for("expenses.view_expense", expense_id=row["id"]))

    return render_template("expenses/new.html", categories=CATEGORIES, form={})


@bp.route("/expenses/<int:expense_id>")
@login_required
def view_expense(expense_id):
    expense = query(
        "SELECT e.*, u.full_name AS owner_name, u.email AS owner_email, u.department AS owner_department, "
        "u.bank_account AS owner_bank_account, d.full_name AS decided_by_name "
        "FROM expenses e JOIN users u ON u.id = e.user_id "
        "LEFT JOIN users d ON d.id = e.decided_by WHERE e.id = %s",
        (expense_id,), one=True,
    )
    if expense is None:
        abort(404)
    comments = query(
        "SELECT c.*, u.full_name FROM comments c JOIN users u ON u.id = c.user_id "
        "WHERE c.expense_id = %s ORDER BY c.created_at",
        (expense_id,),
    )
    return render_template("expenses/view.html", expense=expense, comments=comments)


@bp.route("/expenses/<int:expense_id>/comment", methods=["POST"])
@login_required
def add_comment(expense_id):
    body = request.form.get("body", "").strip()
    if body:
        execute(
            "INSERT INTO comments (expense_id, user_id, body) VALUES (%s, %s, %s)",
            (expense_id, session["user_id"], body),
        )
    return redirect(url_for("expenses.view_expense", expense_id=expense_id))


# GET is allowed so managers can approve straight from the notification email
@bp.route("/expenses/<int:expense_id>/<any(approve, reject):decision>", methods=["GET", "POST"])
@role_required("manager", "admin")
def decide(expense_id, decision):
    status = "approved" if decision == "approve" else "rejected"
    execute(
        "UPDATE expenses SET status = %s, decided_by = %s, decided_at = CURRENT_TIMESTAMP WHERE id = %s",
        (status, session["user_id"], expense_id),
    )
    flash(f"Claim #{expense_id} {status}.", "success")
    return redirect(url_for("expenses.view_expense", expense_id=expense_id))


@bp.route("/approvals")
@role_required("manager", "admin")
def approvals():
    me = query("SELECT department FROM users WHERE id = %s", (session["user_id"],), one=True)
    pending = query(
        "SELECT e.id, e.title, e.amount, e.currency, e.expense_date, u.full_name "
        "FROM expenses e JOIN users u ON u.id = e.user_id "
        "WHERE e.status = 'pending' AND u.department = %s AND e.user_id != %s "
        "ORDER BY e.expense_date",
        (me["department"], session["user_id"]),
    )
    return render_template("expenses/approvals.html", pending=pending, department=me["department"])


@bp.route("/receipts/<path:filename>")
@login_required
def receipt(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
