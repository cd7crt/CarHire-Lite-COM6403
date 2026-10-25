# CarHire Lite

A small car-hire booking web application written in **Python 3 / Flask / SQLite**.
Customers browse cars, get a price, book, look up and cancel bookings. Staff
record pick-ups and returns. Everything is also available as a JSON API.

The full specification (functional requirements, business rules, non-functional
requirements and user stories) is in **[`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md)**.
When the app and the spec disagree, the spec is right.

---

> **Release candidate v1.0.** This build contains deliberately seeded defects.
> A list of them is kept separately so the test team can measure how many it found.

---

## Quick start

You need **Python 3.10 or newer**.

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

# 2. Install dependencies (the -dev file also installs pytest + pytest-cov)
pip install -r requirements-dev.txt

# 3. Run the app
python run.py
```

Open <http://127.0.0.1:5000>. The database (`instance/carhire.sqlite`) is created
automatically the first time the app runs, with 8 sample cars and no bookings.

### Useful commands

| Task | Command |
|------|---------|
| Reset the database to its starting state | `flask --app carhire init-db` |
| Run with a fixed "current date/time" | `CARHIRE_NOW=2026-11-01T09:00 python run.py` (macOS/Linux)<br>`set CARHIRE_NOW=2026-11-01T09:00` then `python run.py` (Windows cmd)<br>`$env:CARHIRE_NOW="2026-11-01T09:00"` then `python run.py` (PowerShell) |

The current system date/time the app is using is shown in the page footer.

---

## Project structure

```
carhire-lite/
├── run.py                  Starts the development server
├── requirements.txt        Runtime dependency (Flask)
├── requirements-dev.txt    + pytest, pytest-cov
├── docs/
│   └── REQUIREMENTS.md     Specification: FRs, business rules, NFRs, user stories
└── carhire/                The application package
    ├── __init__.py         create_app() application factory
    ├── config.py           Settings
    ├── clock.py            Current date/time (can be fixed with CARHIRE_NOW)
    ├── db.py               SQLite connection + init-db command
    ├── schema.sql          Tables + sample cars
    ├── exceptions.py       ValidationError, NotFoundError, UnavailableError, InvalidTransitionError
    ├── pricing.py          Pure functions: quote, discount, refund, late fee
    ├── validation.py       Pure functions: age, dates, name, e-mail, licence checks
    ├── repository.py       All SQL queries (data-access layer)
    ├── services.py         Business logic: create/cancel/pick up/return bookings
    ├── web.py              HTML pages (Flask blueprint)
    ├── api.py              JSON API under /api (Flask blueprint)
    ├── templates/          Jinja2 HTML templates
    └── static/style.css
```

### How the layers fit together

```
  Browser ──▶ web.py ─┐
                      ├──▶ services.py ──▶ validation.py   (pure)
  HTTP/JSON ─▶ api.py ┘         │      ──▶ pricing.py      (pure)
                                └────────▶ repository.py ──▶ db.py ──▶ SQLite
```

- `pricing.py` and `validation.py` have no database or web code. You can call
  them directly with plain Python values.
- `services.py` combines validation, pricing and the repository.
- `web.py` and `api.py` only translate HTTP requests and responses. They call
  `services.py` for all business rules.

---

## Web pages

| URL | Page |
|-----|------|
| `/` | List of cars, with search by make (`/?q=ford`) |
| `/cars/<id>/book` | Booking form for one car |
| `/bookings/find` | Find a booking by reference |
| `/bookings/<reference>` | Booking details, price breakdown and actions (cancel / pick up / return) |
| `/bookings` | Staff list of all bookings |

Key elements have `data-testid` attributes (for example
`data-testid="submit-booking"`, `data-testid="price-total"`,
`data-testid="booking-status"`) so that browser automation tools can find them
reliably.

---

## JSON API

All request and response bodies are JSON. Money values are returned as strings
with 2 decimal places (for example `"252.00"`).

| Method | URL | Body | Success |
|--------|-----|------|---------|
| GET  | `/api/health` | – | 200 `{"status": "ok"}` |
| GET  | `/api/cars` | – (optional `?make=ford`) | 200 list of cars |
| GET  | `/api/cars/<id>` | – | 200 car |
| POST | `/api/quote` | `car_id`, `driver_age`, `pickup_date`, `return_date`, `gps`, `insurance` | 200 `{"car": …, "quote": …}` |
| POST | `/api/bookings` | quote fields + `customer_name`, `customer_email`, `licence_number` | 201 booking |
| GET  | `/api/bookings` | – | 200 list of bookings (newest first) |
| GET  | `/api/bookings/<reference>` | – | 200 booking |
| POST | `/api/bookings/<reference>/cancel` | – | 200 booking (with `refund_amount`) |
| POST | `/api/bookings/<reference>/pickup` | – | 200 booking |
| POST | `/api/bookings/<reference>/return` | `actual_return_date` | 200 booking (with `late_fee`) |

**Error responses**

| Status | When | Body |
|--------|------|------|
| 400 | Validation failed | `{"errors": {"field_name": "message", …}}` |
| 404 | Car or booking not found | `{"error": "message"}` |
| 409 | Car unavailable, or status change not allowed | `{"error": "message"}` |

**Example: create a booking**

```http
POST /api/bookings
Content-Type: application/json

{
  "car_id": 4,
  "customer_name": "Jo Bloggs",
  "customer_email": "jo@example.com",
  "driver_age": 30,
  "licence_number": "BLOGG801017JB9AA",
  "pickup_date": "2026-11-10",
  "return_date": "2026-11-17",
  "gps": false,
  "insurance": true
}
```

---

## Configuration for automated runs

`create_app()` accepts a dictionary of settings that override the defaults.
For example, this runs the app against a separate database file with a fixed
clock:

```python
from carhire import create_app

app = create_app({
    "DATABASE": "/path/to/some-other.sqlite",  # created and filled with sample cars if missing
    "FIXED_NOW": "2026-11-01T09:00",           # the app's "now"
})
client = app.test_client()                     # Flask's built-in HTTP client
```

Setting `"TESTING": True` makes Flask pass exceptions through instead of turning
them into HTTP 500 pages.


## Tests

The `tests/` folder holds the team's automated tests, grouped by member. Install the test tools first:

```
pip install -r requirements-dev.txt
```

Run every test from the project folder with `python -m pytest`. Some tests fail on purpose: v1.0 contains defects, and each failing test is evidence of one. The full results and the defect log are in the team report.

### M3: Black-box unit tests (Christos Dimitriou)

Run the four cases in the report (55 test rows). On v1.0 the expected result is 44 passed and 11 failed:

```
python -m pytest tests/unit/test_m3_assessment.py -v
```

| Case | What it checks | Rows |
|---|---|---:|
| UTB-01 | Driver age limits, category rules and invalid ages | 23 |
| UTB-02 | Worked price example and 16 combinations of discount, surcharge and extras | 17 |
| UTB-09 | Refunds around the 24-hour and 48-hour cutoffs | 8 |
| UTB-10 | Half-up rounding to two decimal places | 7 |

Rows in UTB-02 keep their original UTB-08 IDs.

Run the full M3 regression set (117 rows; expected 100 passed, 17 failed):

```
python -m pytest tests/unit/test_m3_blackbox.py -v
```

Saved results are in `evidence/m3/`. `m3_report/evidence_index.csv` maps each evidence ID used in the report to its file.
