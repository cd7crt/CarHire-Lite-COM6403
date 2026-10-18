"""Business logic: quotes, bookings and the booking status lifecycle.

The web pages (web.py) and the JSON API (api.py) both call these functions,
so the rules are implemented once.
"""
import secrets

from . import pricing, repository
from .exceptions import (
    InvalidTransitionError,
    NotFoundError,
    UnavailableError,
    ValidationError,
)
from .validation import parse_date, validate_booking_request, validate_quote_request

CONFIRMED = "CONFIRMED"
PICKED_UP = "PICKED_UP"
RETURNED = "RETURNED"
CANCELLED = "CANCELLED"


# --------------------------------------------------------------- helpers ----

def _get_car(car_id):
    try:
        car_id = int(car_id)
    except (TypeError, ValueError):
        raise ValidationError({"car_id": "A valid car must be selected."}) from None
    car = repository.get_car(car_id)
    if car is None:
        raise NotFoundError(f"Car {car_id} does not exist.")
    return car


def _get_booking(reference):
    booking = repository.get_booking(str(reference or "").strip().upper())
    if booking is None:
        raise NotFoundError(f"Booking {reference} was not found.")
    return booking


def _new_reference():
    return "CH-" + secrets.token_hex(3).upper()


# ---------------------------------------------------------------- quotes ----

def get_quote(data, today):
    """Validate a quote request and return (car, Quote)."""
    car = _get_car(data.get("car_id"))
    cleaned = validate_quote_request(data, car["category"], today)
    quote = pricing.calculate_quote(
        daily_rate=car["daily_rate"],
        days=pricing.rental_days(cleaned["pickup_date"], cleaned["return_date"]),
        driver_age=cleaned["driver_age"],
        gps=cleaned["gps"],
        insurance=cleaned["insurance"],
    )
    return car, quote


# -------------------------------------------------------------- bookings ----

def create_booking(data, now):
    """Validate, check availability, price and save a new booking."""
    car = _get_car(data.get("car_id"))
    cleaned = validate_booking_request(data, car["category"], now.date())

    clashes = repository.count_overlapping_bookings(
        car["id"], cleaned["pickup_date"], cleaned["return_date"]
    )
    if clashes > 0:
        raise UnavailableError(
            "Sorry, this car is already booked for some or all of those dates."
        )

    quote = pricing.calculate_quote(
        daily_rate=car["daily_rate"],
        days=pricing.rental_days(cleaned["pickup_date"], cleaned["return_date"]),
        driver_age=cleaned["driver_age"],
        gps=cleaned["gps"],
        insurance=cleaned["insurance"],
    )

    reference = _new_reference()
    repository.insert_booking(
        {
            "reference": reference,
            "car_id": car["id"],
            "customer_name": cleaned["customer_name"],
            "customer_email": cleaned["customer_email"],
            "driver_age": cleaned["driver_age"],
            "licence_number": cleaned["licence_number"],
            "pickup_date": cleaned["pickup_date"].isoformat(),
            "return_date": cleaned["return_date"].isoformat(),
            "gps": int(cleaned["gps"]),
            "insurance": int(cleaned["insurance"]),
            "days": quote.days,
            "base_price": str(quote.base),
            "discount": str(quote.discount),
            "surcharge": str(quote.surcharge),
            "extras_price": str(quote.extras),
            "total_price": str(quote.total),
            "created_at": now.isoformat(timespec="seconds"),
        }
    )
    return repository.get_booking(reference)


def get_booking(reference):
    return _get_booking(reference)


def list_bookings():
    return repository.list_bookings()


def cancel_booking(reference, now):
    """Cancel a booking and record the refund due."""
    booking = _get_booking(reference)
    if booking["status"] in (CANCELLED, RETURNED):
        raise InvalidTransitionError(
            f"A {booking['status'].lower()} booking cannot be cancelled."
        )

    hours = pricing.hours_until_pickup(parse_date(booking["pickup_date"]), now)
    refund = pricing.calculate_refund(booking["total_price"], hours)
    repository.record_cancellation(booking["reference"], refund)
    return repository.get_booking(booking["reference"])


def pick_up(reference):
    """Record that the customer has collected the car."""
    booking = _get_booking(reference)
    if booking["status"] != CONFIRMED:
        raise InvalidTransitionError(
            f"Only confirmed bookings can be picked up (this one is {booking['status']})."
        )
    repository.set_status(booking["reference"], PICKED_UP)
    return repository.get_booking(booking["reference"])


def return_car(reference, actual_return_date):
    """Record the car's return and charge any late fee."""
    booking = _get_booking(reference)
    if booking["status"] != PICKED_UP:
        raise InvalidTransitionError(
            f"Only picked-up bookings can be returned (this one is {booking['status']})."
        )

    actual = parse_date(actual_return_date)
    if actual is None:
        raise ValidationError(
            {"actual_return_date": "Return date must be a valid date (YYYY-MM-DD)."}
        )
    if actual < parse_date(booking["pickup_date"]):
        raise ValidationError(
            {"actual_return_date": "Return date cannot be before the pick-up date."}
        )

    late_fee = pricing.calculate_late_fee(
        booking["daily_rate"], parse_date(booking["return_date"]), actual
    )
    repository.record_return(booking["reference"], actual, late_fee)
    return repository.get_booking(booking["reference"])


# --------------------------------------------------------- serialisation ----

def car_to_dict(car):
    return {
        "id": car["id"],
        "make": car["make"],
        "model": car["model"],
        "category": car["category"],
        "seats": car["seats"],
        "daily_rate": f"{car['daily_rate']:.2f}",
    }


def booking_to_dict(booking):
    return {
        "reference": booking["reference"],
        "status": booking["status"],
        "car": {
            "id": booking["car_id"],
            "make": booking["make"],
            "model": booking["model"],
            "category": booking["category"],
            "daily_rate": f"{booking['daily_rate']:.2f}",
        },
        "customer_name": booking["customer_name"],
        "customer_email": booking["customer_email"],
        "driver_age": booking["driver_age"],
        "licence_number": booking["licence_number"],
        "pickup_date": booking["pickup_date"],
        "return_date": booking["return_date"],
        "gps": bool(booking["gps"]),
        "insurance": bool(booking["insurance"]),
        "price": {
            "days": booking["days"],
            "base": booking["base_price"],
            "discount": booking["discount"],
            "surcharge": booking["surcharge"],
            "extras": booking["extras_price"],
            "total": booking["total_price"],
        },
        "refund_amount": booking["refund_amount"],
        "actual_return_date": booking["actual_return_date"],
        "late_fee": booking["late_fee"],
        "created_at": booking["created_at"],
    }
