# vulnerable_application: Utlegg

> ⚠️ **This application is intentionally insecure.** It exists so I can practise and document a penetration test. Run it only on your own machine. Never deploy it to a public server or expose it to a network you don't control.

**Utlegg** is an expense-claims web app for a fictional company, *Nordvik Demo AS*. Employees submit claims with receipts, managers approve or reject them, and administrators manage users and export claims for accounting.

The application contains security flaws of the kind that come from ordinary human error and misconfiguration, not CTF-style puzzles. The goal of this project is to:

1. Run a structured penetration test against it
2. Write a professional report with findings, severity ratings and recommendations
3. Fix each finding in its own pull request
4. Retest and document the before and after

The pentest report and remediation history will be linked here once they are published.

## Tech stack

- Python 3.12 / Flask
- PostgreSQL 16
- Docker Compose

## Running it

### With Docker (recommended)

```bash
docker compose up --build
```

Then open <http://127.0.0.1:5000>.

To reset everything (database and uploaded receipts):

```bash
docker compose down -v
```

### Without Docker (SQLite)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=sqlite:///utlegg.db      # PowerShell: $env:DATABASE_URL="sqlite:///utlegg.db"
flask --app utlegg init-db
flask --app utlegg run --debug
```

## Test scope (grey box)

Accounts provided to the tester:

| Role | Email | Password |
|---|---|---|
| Employee | `emma.nilsen@nordvik.test` | `emma2024` |
| Employee | `jonas.dahl@nordvik.test` | `Passord1` |
| Manager (Sales) | `lars.haugen@nordvik.test` | `Sommer2024` |

**In scope:** the web application at `http://127.0.0.1:5000` and its source code in this repository.
**Out of scope:** denial of service, and the host machine outside the containers.

Password reset emails are written to the application log (`docker compose logs web`) because there is no mail server in the lab.

## Project structure

```
utlegg/
  __init__.py      app factory
  auth.py          login, logout, password reset
  expenses.py      claims, receipts, comments, approvals
  profile.py       user profile
  admin.py         user management, CSV export
  internal.py      ops status endpoint
  db.py            database helper (Postgres / SQLite)
  schema.sql       tables
  seed.py          fictional demo data
  templates/       Jinja2 templates
  static/          CSS
```

All names, accounts, bank details and amounts in the demo data are fictional.
