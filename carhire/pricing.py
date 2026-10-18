"""Price, refund and late-fee calculations.

Every function here is *pure*: it uses only its arguments, never the database
or the clock.
"""
from dataclasses import dataclass
from datetime import datetime, time
from decimal import ROUND_HALF_UP, Decimal

PICKUP_TIME = time(10, 0)

YOUNG_DRIVER_MAX_AGE = 24
YOUNG_DRIVER_SURCHARGE_PER_DAY = Decimal("15.00")
GPS_PER_DAY = Decimal("5.00")
INSURANCE_PER_DAY = Decimal("12.00")
LATE_FEE_MULTIPLIER = Decimal("1.5")

ZERO = Decimal("0.00")


def money(value):
    """Round a value to pounds and pence (2 d.p., half-up)."""
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Quote:
    days: int
    base: Decimal
    discount: Decimal
    surcharge: Decimal
    extras: Decimal
    total: Decimal

    def as_dict(self):
        return {
            "days": self.days,
            "base": str(self.base),
            "discount": str(self.discount),
            "surcharge": str(self.surcharge),
            "extras": str(self.extras),
            "total": str(self.total),
        }


def rental_days(pickup_date, return_date):
    """Number of rental days between two dates."""
    return (return_date - pickup_date).days


def discount_rate(days):
    """Long-rental discount rate for a rental of ``days`` days."""
    if days > 14:
        return Decimal("0.20")
    if days >= 7:
        return Decimal("0.10")
    return Decimal("0")


def calculate_quote(daily_rate, days, driver_age, gps=False, insurance=False):
    """Return a full price breakdown for a rental."""
    base = money(Decimal(daily_rate) * days)
    discount = money(base * discount_rate(days))

    surcharge = ZERO
    if driver_age <= YOUNG_DRIVER_MAX_AGE:
        surcharge = YOUNG_DRIVER_SURCHARGE_PER_DAY

    extras = ZERO
    if gps:
        extras += GPS_PER_DAY * days
    if insurance:
        extras += INSURANCE_PER_DAY * days

    total = base - discount + surcharge + extras
    return Quote(days, base, discount, money(surcharge), money(extras), money(total))


def hours_until_pickup(pickup_date, now):
    """Hours from ``now`` until 10:00 on the pick-up date (negative if passed)."""
    pickup_at = datetime.combine(pickup_date, PICKUP_TIME)
    return (pickup_at - now).total_seconds() / 3600


def refund_percentage(hours_before_pickup):
    """Percentage of the total refunded when cancelling."""
    if hours_before_pickup >= 24:
        return 50
    elif hours_before_pickup >= 48:
        return 100
    return 0


def calculate_refund(total, hours_before_pickup):
    """Refund amount for a cancellation."""
    percentage = refund_percentage(hours_before_pickup)
    return money(Decimal(total) * percentage / 100)


def calculate_late_fee(daily_rate, due_date, actual_return_date):
    """Fee for returning a car after its agreed return date."""
    late_days = (actual_return_date - due_date).days
    if late_days <= 0:
        return ZERO
    return money(Decimal(daily_rate) * late_days * LATE_FEE_MULTIPLIER)
