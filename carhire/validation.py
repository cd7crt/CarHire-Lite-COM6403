"""Input validation for quotes and bookings."""
import re
from datetime import date

from .exceptions import ValidationError

MIN_DRIVER_AGE = 21
MAX_DRIVER_AGE = 75
MIN_LUXURY_AGE = 25
MIN_RENTAL_DAYS = 1
MAX_RENTAL_DAYS = 28
NAME_MIN_LENGTH = 2
NAME_MAX_LENGTH = 50

EMAIL_PATTERN = re.compile(r"^[^@]+@[^@]+$")
LICENCE_PATTERN = re.compile(r"^[A-Za-z0-9]{16}$")


# ---------------------------------------------------------------------------
# Converters: turn raw input (strings from a form or JSON values) into types.
# They return None when the value cannot be converted.
# ---------------------------------------------------------------------------

def parse_date(value):
    """Parse a YYYY-MM-DD string into a date."""
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value).strip())
    except (TypeError, ValueError):
        return None


def parse_age(value):
    """Parse a whole-number age."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip() if value is not None else ""
    if text.isdigit():
        return int(text)
    return None


def to_bool(value):
    """Interpret checkbox / JSON values such as True, "true", "on", "1"."""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "on", "1", "yes"}


# ---------------------------------------------------------------------------
# Rule checks: each returns an error message, or None when the value is valid.
# ---------------------------------------------------------------------------

def check_driver_age(age, category):
    if not MIN_DRIVER_AGE < age <= MAX_DRIVER_AGE:
        return f"Driver must be aged between {MIN_DRIVER_AGE} and {MAX_DRIVER_AGE}."
    if category == "LUXURY" and age < MIN_LUXURY_AGE:
        return f"Drivers must be at least {MIN_LUXURY_AGE} to hire a luxury car."
    return None


def check_pickup_date(pickup_date, today):
    if pickup_date < today:
        return "Pick-up date cannot be in the past."
    return None


def check_return_date(pickup_date, return_date):
    days = (return_date - pickup_date).days
    if days < MIN_RENTAL_DAYS:
        return "Return date must be after the pick-up date."
    if days > MAX_RENTAL_DAYS:
        return f"Rentals cannot be longer than {MAX_RENTAL_DAYS} days."
    return None


def check_name(name):
    length = len(name.strip())
    if length < NAME_MIN_LENGTH or length > NAME_MAX_LENGTH:
        return f"Name must be {NAME_MIN_LENGTH} to {NAME_MAX_LENGTH} characters."
    return None


def is_valid_email(email):
    return bool(EMAIL_PATTERN.match(email.strip()))


def is_valid_licence(licence):
    return bool(LICENCE_PATTERN.match(licence.strip()))


# ---------------------------------------------------------------------------
# Request validators: check a whole request and return cleaned values.
# ---------------------------------------------------------------------------

def validate_quote_request(data, category, today):
    """Validate the fields needed for a price quote.

    Returns a dict with ``driver_age``, ``pickup_date``, ``return_date``,
    ``gps`` and ``insurance`` converted to Python types, or raises
    ValidationError listing every problem found.
    """
    errors = {}

    age = parse_age(data.get("driver_age"))
    if age is None:
        errors["driver_age"] = "Driver age must be a whole number."
    else:
        message = check_driver_age(age, category)
        if message:
            errors["driver_age"] = message

    pickup_date = parse_date(data.get("pickup_date"))
    return_date = parse_date(data.get("return_date"))
    if pickup_date is None:
        errors["pickup_date"] = "Pick-up date must be a valid date (YYYY-MM-DD)."
    else:
        message = check_pickup_date(pickup_date, today)
        if message:
            errors["pickup_date"] = message
    if return_date is None:
        errors["return_date"] = "Return date must be a valid date (YYYY-MM-DD)."
    elif pickup_date is not None:
        message = check_return_date(pickup_date, return_date)
        if message:
            errors["return_date"] = message

    if errors:
        raise ValidationError(errors)

    return {
        "driver_age": age,
        "pickup_date": pickup_date,
        "return_date": return_date,
        "gps": to_bool(data.get("gps", False)),
        "insurance": to_bool(data.get("insurance", False)),
    }


def validate_booking_request(data, category, today):
    """Validate a full booking request (quote fields plus customer details)."""
    errors = {}
    cleaned = {}
    try:
        cleaned = validate_quote_request(data, category, today)
    except ValidationError as exc:
        errors.update(exc.errors)

    name = str(data.get("customer_name") or "")
    email = str(data.get("customer_email") or "")
    licence = str(data.get("licence_number") or "")

    message = check_name(name)
    if message:
        errors["customer_name"] = message
    if not is_valid_email(email):
        errors["customer_email"] = "Enter a valid e-mail address, e.g. jo@example.com."
    if not is_valid_licence(licence):
        errors["licence_number"] = "Licence number must be exactly 16 letters or digits."

    if errors:
        raise ValidationError(errors)

    cleaned.update(
        customer_name=name.strip(),
        customer_email=email.strip(),
        licence_number=licence.strip().upper(),
    )
    return cleaned
