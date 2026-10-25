from datetime import date, datetime
from decimal import Decimal

import pytest

from carhire.pricing import (
    calculate_late_fee,
    calculate_quote,
    calculate_refund,
    discount_rate,
    hours_until_pickup,
    rental_days,
    refund_percentage,
)


@pytest.mark.parametrize(
    ("days", "expected_rate"),
    [
        (1, Decimal("0")),
        (6, Decimal("0")),
        (7, Decimal("0.10")),
        (13, Decimal("0.10")),
        (14, Decimal("0.20")),
        (28, Decimal("0.20")),
    ],
)
def test_discount_rate_boundaries(days, expected_rate):
    assert discount_rate(days) == expected_rate


def test_calculate_quote_applies_discount_only_to_base_and_prices_extras_per_day():
    quote = calculate_quote(
        daily_rate=Decimal("100.00"),
        days=7,
        driver_age=30,
        gps=True,
        insurance=True,
    )

    assert quote.days == 7
    assert quote.base == Decimal("700.00")
    assert quote.discount == Decimal("70.00")
    assert quote.surcharge == Decimal("0.00")
    assert quote.extras == Decimal("119.00")
    assert quote.total == Decimal("749.00")


def test_calculate_quote_charges_young_driver_surcharge_per_day():
    quote = calculate_quote(daily_rate="40.00", days=3, driver_age=21)

    assert quote.surcharge == Decimal("45.00")
    assert quote.total == Decimal("165.00")


@pytest.mark.parametrize(
    ("driver_age", "expected_surcharge"),
    [
        (21, Decimal("15.00")),
        (24, Decimal("15.00")),
        (25, Decimal("0.00")),
    ],
)
def test_calculate_quote_young_driver_age_boundaries(driver_age, expected_surcharge):
    quote = calculate_quote(daily_rate="20.00", days=1, driver_age=driver_age)

    assert quote.surcharge == expected_surcharge


def test_calculate_quote_rounds_money_half_up_and_serializes_breakdown():
    quote = calculate_quote(daily_rate="0.335", days=1, driver_age=30)

    assert quote.base == Decimal("0.34")
    assert quote.as_dict() == {
        "days": 1,
        "base": "0.34",
        "discount": "0.00",
        "surcharge": "0.00",
        "extras": "0.00",
        "total": "0.34",
    }


def test_rental_days_returns_difference_between_dates():
    assert rental_days(date(2026, 11, 10), date(2026, 11, 17)) == 7


def test_hours_until_pickup_uses_ten_am_pickup_time():
    assert hours_until_pickup(
        date(2026, 11, 10), datetime(2026, 11, 8, 10, 0)
    ) == 48


@pytest.mark.parametrize(
    ("hours_before_pickup", "expected_percentage"),
    [
        (48, 100),
        (72, 100),
        (47.99, 50),
        (24, 50),
        (23.99, 0),
        (0, 0),
        (-1, 0),
    ],
)
def test_refund_percentage_boundaries(hours_before_pickup, expected_percentage):
    assert refund_percentage(hours_before_pickup) == expected_percentage


def test_calculate_refund_returns_full_amount_at_least_48_hours_before_pickup():
    assert calculate_refund("123.45", 48) == Decimal("123.45")


def test_calculate_refund_rounds_half_up():
    assert calculate_refund("10.01", 24) == Decimal("5.01")


@pytest.mark.parametrize(
    ("actual_return_date", "expected_fee"),
    [
        (date(2026, 11, 9), Decimal("0.00")),
        (date(2026, 11, 10), Decimal("0.00")),
        (date(2026, 11, 11), Decimal("60.00")),
        (date(2026, 11, 12), Decimal("120.00")),
    ],
)
def test_calculate_late_fee(actual_return_date, expected_fee):
    assert (
        calculate_late_fee(
            daily_rate="40.00",
            due_date=date(2026, 11, 10),
            actual_return_date=actual_return_date,
        )
        == expected_fee
    )