"""Demo data. All people, accounts and amounts are fictional."""
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

from .db import execute

USERS = [
    # email, password, name, department, role, phone, bank account
    ("admin@nordvik.test", "admin123", "System Administrator", "IT", "admin", None, None),
    ("ingrid.berg@nordvik.test", "Fjord2024!", "Ingrid Berg", "Finance", "manager", "+47 400 00 101", "1234.56.78901"),
    ("lars.haugen@nordvik.test", "Sommer2024", "Lars Haugen", "Sales", "manager", "+47 400 00 102", "1234.56.78902"),
    ("emma.nilsen@nordvik.test", "emma2024", "Emma Nilsen", "Sales", "employee", "+47 400 00 103", "1234.56.78903"),
    ("jonas.dahl@nordvik.test", "Passord1", "Jonas Dahl", "Sales", "employee", "+47 400 00 104", "1234.56.78904"),
    ("sara.lie@nordvik.test", "Bergen123", "Sara Lie", "Finance", "employee", "+47 400 00 105", "1234.56.78905"),
    ("ole.moen@nordvik.test", "oleole99", "Ole Moen", "IT", "employee", "+47 400 00 106", "1234.56.78906"),
]

EXPENSES = [
    # user index, title, category, amount, days ago, status, description
    (3, "Client lunch with Hydro team", "Meals", 1240.00, 3, "pending", "Lunch meeting about the Q1 renewal."),
    (3, "Train Bergen–Oslo", "Travel", 899.00, 12, "approved", "Customer workshop in Oslo."),
    (3, "Hotel Oslo, 1 night", "Accommodation", 1650.00, 12, "approved", None),
    (4, "Taxi from airport", "Travel", 720.00, 5, "pending", "Late flight, no airport bus."),
    (4, "Conference ticket – NDC Oslo", "Training", 9800.00, 20, "rejected", "Rejected: not in this year's budget."),
    (5, "Accounting software licence", "Software", 2399.00, 8, "pending", "Annual licence renewal."),
    (5, "Team dinner", "Meals", 3450.00, 30, "approved", "Year-end dinner, 6 people."),
    (6, "USB-C docking station", "Equipment", 1899.00, 2, "pending", "Replacement for broken dock."),
    (1, "Flight to Stockholm", "Travel", 2150.00, 15, "pending", "Nordic finance meetup."),
    (2, "Customer gift baskets", "Other", 4200.00, 9, "pending", "Christmas gifts for top 10 customers."),
]

COMMENTS = [
    (1, 2, "Please attach the receipt from the restaurant."),
    (1, 3, "Uploaded now, thanks!"),
    (5, 2, "We can revisit this in Q2."),
]


def seed_data():
    user_ids = []
    for email, pw, name, dept, role, phone, bank in USERS:
        row = execute(
            "INSERT INTO users (email, password_hash, full_name, department, role, phone, bank_account) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (email, generate_password_hash(pw), name, dept, role, phone, bank),
            returning=True,
        )
        user_ids.append(row["id"])

    expense_ids = []
    today = date.today()
    for uidx, title, cat, amount, days_ago, status, desc in EXPENSES:
        decided_by = user_ids[1] if status != "pending" else None
        row = execute(
            "INSERT INTO expenses (user_id, title, description, category, amount, expense_date, status, decided_by) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (user_ids[uidx], title, desc, cat, amount, today - timedelta(days=days_ago), status, decided_by),
            returning=True,
        )
        expense_ids.append(row["id"])

    for eidx, uidx, body in COMMENTS:
        execute(
            "INSERT INTO comments (expense_id, user_id, body) VALUES (%s, %s, %s)",
            (expense_ids[eidx - 1], user_ids[uidx], body),
        )
