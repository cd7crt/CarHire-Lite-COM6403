"""Data-access layer: every SQL statement in the application lives here."""
from .db import get_db

BOOKING_SELECT = """
    SELECT b.*, c.make, c.model, c.category, c.daily_rate
    FROM bookings b
    JOIN cars c ON c.id = b.car_id
"""


# ----------------------------------------------------------------- cars ----

def list_cars():
    return get_db().execute("SELECT * FROM cars ORDER BY daily_rate, id").fetchall()


def search_cars(make):
    """Cars whose make contains ``make`` (case-insensitive)."""
    sql = f"SELECT * FROM cars WHERE make LIKE '%{make}%' ORDER BY daily_rate, id"
    return get_db().execute(sql).fetchall()


def get_car(car_id):
    return get_db().execute("SELECT * FROM cars WHERE id = ?", (car_id,)).fetchone()


# ------------------------------------------------------------- bookings ----

def count_overlapping_bookings(car_id, pickup_date, return_date):
    """How many active bookings for this car overlap the requested period."""
    sql = """
        SELECT COUNT(*) FROM bookings
        WHERE car_id = ?
          AND status IN ('CONFIRMED', 'PICKED_UP')
          AND (
                (pickup_date <= ? AND ? < return_date)
             OR (pickup_date < ? AND ? <= return_date)
          )
    """
    start, end = pickup_date.isoformat(), return_date.isoformat()
    row = get_db().execute(sql, (car_id, start, start, end, end)).fetchone()
    return row[0]


def insert_booking(booking):
    conn = get_db()
    conn.execute(
        """
        INSERT INTO bookings (
            reference, car_id, customer_name, customer_email, driver_age,
            licence_number, pickup_date, return_date, gps, insurance, days,
            base_price, discount, surcharge, extras_price, total_price,
            status, created_at
        ) VALUES (
            :reference, :car_id, :customer_name, :customer_email, :driver_age,
            :licence_number, :pickup_date, :return_date, :gps, :insurance, :days,
            :base_price, :discount, :surcharge, :extras_price, :total_price,
            'CONFIRMED', :created_at
        )
        """,
        booking,
    )
    conn.commit()


def get_booking(reference):
    sql = BOOKING_SELECT + " WHERE b.reference = ?"
    return get_db().execute(sql, (reference,)).fetchone()


def list_bookings():
    sql = BOOKING_SELECT + " ORDER BY b.created_at DESC, b.id DESC"
    return get_db().execute(sql).fetchall()


def set_status(reference, status):
    conn = get_db()
    conn.execute("UPDATE bookings SET status = ? WHERE reference = ?", (status, reference))
    conn.commit()


def record_cancellation(reference, refund_amount):
    conn = get_db()
    conn.execute(
        "UPDATE bookings SET status = 'CANCELLED', refund_amount = ? WHERE reference = ?",
        (str(refund_amount), reference),
    )
    conn.commit()


def record_return(reference, actual_return_date, late_fee):
    conn = get_db()
    conn.execute(
        """
        UPDATE bookings
        SET status = 'RETURNED', actual_return_date = ?, late_fee = ?
        WHERE reference = ?
        """,
        (actual_return_date.isoformat(), str(late_fee), reference),
    )
    conn.commit()
