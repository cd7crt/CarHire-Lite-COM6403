"""Test inputs and expected results based on the CarHire Lite requirements."""
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import importlib
from pathlib import Path
import sys
import types

# The full set has 117 test rows.
# test_m3_assessment.py uses four of these cases for the report.

# Keep the dates fixed so the tests give the same results when run later.
ROOT = Path(__file__).resolve().parents[2]
TODAY = date(2026, 11, 1)
PICKUP = date(2026, 11, 10)


def load_units():
    # Load the functions without starting Flask or opening the database.
    # Use a separate package name so the relative imports still work.
    name = "_carhire_m3_unit_target"
    if name not in sys.modules:
        package = types.ModuleType(name)
        package.__path__ = [str(ROOT / "carhire")]
        sys.modules[name] = package
    return tuple(importlib.import_module(name + "." + part)
                 for part in ("validation", "pricing", "exceptions"))


def quote_input(**changes):
    # Start with a valid seven-day quote and change the input being tested.
    # Keep the other inputs valid so they do not affect the result.
    data = dict(driver_age="30", pickup_date="2026-11-10",
                return_date="2026-11-17", gps=False, insurance=False)
    data.update(changes)
    return data


def booking_input(**changes):
    # Use sample customer details that meet BR-12 for the booking tests.
    # Each test changes only the customer detail it needs to check.
    data = quote_input()
    data.update(customer_name="Jo Bloggs", customer_email="jo@example.com",
                licence_number="ABCD1234EFGH5678")
    data.update(changes)
    return data


def pounds(value):
    # Use Decimal to avoid float rounding errors in the expected amounts.
    # Round half up as required and keep two decimal places in the result.
    return str(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def expected_quote(rate, days, age, gps=False, insurance=False):
    """Calculate the expected price using BR-04 to BR-07."""
    # Calculate the expected price separately from the app.
    # This stops a bug in the app from also changing the expected result.
    base = Decimal(str(rate)) * days
    # BR-05 gives 0% off for 1-6 days, 10% for 7-13 and 20% from 14 days.
    # Check the longest rental first and apply the discount to the base price only.
    percent = Decimal("0.20") if days >= 14 else Decimal("0.10") if days >= 7 else Decimal("0")
    discount = base * percent
    # BR-06 and BR-07 charge the surcharge and selected extras for each day.
    # Add the daily cost of each extra only when it is selected.
    surcharge = Decimal("15") * days if 21 <= age <= 24 else Decimal("0")
    extras = (Decimal("5") * bool(gps) + Decimal("12") * bool(insurance)) * days
    return dict(days=days, base=pounds(base), discount=pounds(discount),
                surcharge=pounds(surcharge), extras=pounds(extras),
                total=pounds(base - discount + surcharge + extras))


CASES = []


def add(case, row, rules, technique, objective, kind, inputs, expected):
    # case_id groups the tests and row_id identifies each input row.
    # Save the rule IDs and use kind to choose which function to test.
    CASES.append(dict(case_id=case, row_id=f"{case}-{row}", requirements=rules,
                      technique=technique, objective=objective, kind=kind,
                      inputs=inputs, expected=expected))


def validation_row(case, row, rules, objective, data, valid, category="ECONOMY", booking=False, **normalised):
    # valid says whether the input should be accepted.
    # Rejecting an invalid input counts as a pass when that is the expected result.
    add(case, row, rules, "Equivalence partitioning / boundary values / decision table",
        objective, "booking" if booking else "validation",
        dict(data=data, category=category, today=TODAY.isoformat()),
        dict(valid=valid, **normalised))


# UTB-01 checks driver eligibility with 23 rows using BR-01 and BR-02.
# Check around ages 21 and 75, and the minimum age of 25 for LUXURY cars.
for category in ("ECONOMY", "LUXURY"):
    for age in (20, 21, 22, 24, 25, 26, 74, 75, 76):
        valid = 21 <= age <= 75 and (category != "LUXURY" or age >= 25)
        validation_row("UTB-01", f"{category.lower()}-{age}", ["BR-01", "BR-02"],
                       f"Eligibility at age {age} for {category}", quote_input(driver_age=str(age)), valid, category)
for label, raw in [("fraction-text", "21.5"), ("fraction-number", 21.5),
                   ("letters", "abc"), ("empty", ""), ("missing", None)]:
    validation_row("UTB-01", label, ["BR-01"], "Reject a non-whole or missing age", quote_input(driver_age=raw), False)

# UTB-02 checks the worked example from the requirements in one row.
# At age 30 with no extras, 7 days at GBP 40 gives GBP 280 minus GBP 28, totalling GBP 252.
add("UTB-02", "worked-example", ["BR-04", "BR-05", "BR-06", "BR-07"], "Valid equivalence partition",
    "The specification's £40/day, seven-day worked example", "quote",
    dict(daily_rate="40.00", days=7, driver_age=30, gps=False, insurance=False),
    dict(days=7, base="280.00", discount="28.00", surcharge="0.00", extras="0.00", total="252.00"))

# UTB-03 checks pickup dates, rental length and date format with 15 rows for BR-03.
# Try yesterday, today and tomorrow to check the earliest allowed pickup date.
for offset, label, valid in [(-1, "yesterday", False), (0, "today", True), (1, "tomorrow", True)]:
    pickup = TODAY + timedelta(days=offset)
    validation_row("UTB-03", label, ["BR-03"], "Pickup date relative to fixed today",
                   quote_input(pickup_date=pickup.isoformat(), return_date=(pickup + timedelta(days=1)).isoformat()), valid)
for days in (-1, 0, 1, 2, 27, 28, 29):
    validation_row("UTB-03", f"length-{days}", ["BR-03"], "Rental length boundaries",
                   quote_input(return_date=(PICKUP + timedelta(days=days)).isoformat()), 1 <= days <= 28)
for label, bad in [("impossible-date", "2026-02-30"), ("words", "not-a-date"),
                   ("empty-date", ""), ("unpadded-date", "2026-11-1"), ("compact-date", "20261110")]:
    validation_row("UTB-03", label, ["BR-03"], "Reject a date outside YYYY-MM-DD", quote_input(pickup_date=bad), False)

# UTB-04 uses 11 rows to check name length after removing outer spaces for BR-12.
# Try 1, 2, 3, 49, 50 and 51 characters, plus names with spaces at either end.
for length in (1, 2, 3, 49, 50, 51):
    validation_row("UTB-04", f"length-{length}", ["BR-12"], "Name length after trimming",
                   booking_input(customer_name="A" * length), 2 <= length <= 50, booking=True)
for label, name, valid in [("trimmed-two", "  Jo  ", True), ("trimmed-one", "  J  ", False),
                           ("trimmed-fifty", "  " + "A" * 50 + "  ", True), ("spaces", "   ", False), ("empty", "", False)]:
    validation_row("UTB-04", label, ["BR-12"], "Name trimming and empty partition",
                   booking_input(customer_name=name), valid, booking=True)

# UTB-05 uses 11 rows to check valid and invalid email groups for BR-12.
# Try missing parts, extra @ signs, no domain dot, spaces and an empty email.
for label, email, valid in [("valid", "jo@example.com", True), ("short-valid", "a@b.c", True),
                            ("no-at", "jo.example.com", False), ("two-at", "jo@@example.com", False),
                            ("no-local", "@example.com", False), ("no-domain", "jo@", False),
                            ("no-dot", "jo@example", False), ("leading-space", " jo@example.com", False),
                            ("internal-space", "jo @example.com", False), ("trailing-space", "jo@example.com ", False),
                            ("empty", "", False)]:
    validation_row("UTB-05", label, ["BR-12"], "Email partitions from the stated grammar",
                   booking_input(customer_email=email), valid, booking=True)

# UTB-06 uses 9 rows to check licence length, allowed characters and case for BR-12.
# Try 15, 16 and 17 characters and check that lowercase letters become uppercase.
for label, licence, valid in [("length-15", "A" * 15, False), ("letters-16", "A" * 16, True),
                              ("length-17", "A" * 17, False), ("digits-16", "1" * 16, True),
                              ("mixed-16", "ABCD1234EFGH5678", True), ("lowercase-16", "abcd1234efgh5678", True),
                              ("punctuation", "ABCD1234EFGH567!", False), ("space", "ABCD1234EFGH567 ", False),
                              ("empty", "", False)]:
    normalised = {"licence_number": licence.upper()} if valid else {}
    validation_row("UTB-06", label, ["BR-12"], "Licence length, character set and uppercase normalisation",
                   booking_input(licence_number=licence), valid, booking=True, **normalised)

# UTB-07 uses 8 rows to check around the 7-day and 14-day discounts for BR-05.
# Keep the rate, age and extras the same so only the rental length changes.
for days in (1, 6, 7, 8, 13, 14, 15, 28):
    add("UTB-07", f"days-{days}", ["BR-04", "BR-05"], "Boundary value analysis",
        "Discount thresholds with age and extras held constant", "quote",
        dict(daily_rate="40.00", days=days, driver_age=30, gps=False, insurance=False), expected_quote("40.00", days, 30))

# UTB-08 checks 16 combinations of age, rental length, GPS and insurance.
# Use ages 24 and 25 with 6 and 7 days to check the surcharge and discount cutoffs.
# Discount the base price only and charge extras and the surcharge for each day.
for age in (24, 25):
    for days in (6, 7):
        for gps in (False, True):
            for insurance in (False, True):
                add("UTB-08", f"age-{age}-days-{days}-gps-{int(gps)}-ins-{int(insurance)}",
                    ["BR-04", "BR-05", "BR-06", "BR-07"], "Full 16-rule decision table",
                    "Discount applies to base only; surcharge and extras are daily", "quote",
                    dict(daily_rate="40.00", days=days, driver_age=age, gps=gps, insurance=insurance),
                    expected_quote("40.00", days, age, gps, insurance))

# UTB-09 checks one minute below, exactly at and one minute above each refund cutoff.
# Use a GBP 100 booking so the refund percentages are easy to check.
# Check pickup timing separately in the clock rows. These do not test booking status.
for label, minutes, amount in [("48h-plus-1m", 2881, "100.00"), ("48h", 2880, "100.00"),
                                ("48h-minus-1m", 2879, "50.00"), ("24h-plus-1m", 1441, "50.00"),
                                ("24h", 1440, "50.00"), ("24h-minus-1m", 1439, "0.00"),
                                ("at-pickup", 0, "0.00"), ("after-pickup", -60, "0.00")]:
    hours = minutes / 60
    add("UTB-09", "refund-" + label, ["BR-08"], "Boundary value analysis",
        "Refund percentage at 24/48-hour boundaries", "refund", dict(total="100.00", hours=hours), amount)
    now = datetime(2026, 11, 10, 10, 0) - timedelta(minutes=minutes)
    add("UTB-09", "clock-" + label, ["BR-08"], "Boundary value analysis",
        "Pickup is at 10:00 on the specified date", "hours", dict(pickup=PICKUP.isoformat(), now=now.isoformat()), hours)

# UTB-10 uses 7 rows to check half-up rounding to two decimal places for BR-07.
# Check values around half a penny and that 99.995 rounds up to 100.00.
for value, expected in [("0.004", "0.00"), ("0.005", "0.01"), ("1.004", "1.00"),
                         ("1.005", "1.01"), ("1.006", "1.01"), ("2.675", "2.68"), ("99.995", "100.00")]:
    add("UTB-10", value.replace(".", "p"), ["BR-07"], "Boundary value analysis",
        "Round exact decimal money half-up to two places", "money", dict(value=value), expected)


def observe(case):
    # Pass the test input to the app function and record the result.
    # Keep the expected result unchanged so the comparison can show any problems.
    validation, pricing, exceptions = load_units()
    data = case["inputs"]
    if case["kind"] in ("validation", "booking"):
        method = validation.validate_booking_request if case["kind"] == "booking" else validation.validate_quote_request
        try:
            # Pass a copy so the app cannot change the saved test inputs.
            result = method(dict(data["data"]), data["category"], date.fromisoformat(data["today"]))
        except exceptions.ValidationError as error:
            # Record rejected inputs so they can be compared with the expected result.
            # Let pytest report any other exceptions.
            return dict(valid=False, errors=error.errors)
        answer = dict(valid=True, returned=result)
        for key in case["expected"]:
            # Include cleaned fields when the test has an expected value for them.
            if key != "valid":
                answer[key] = result.get(key) if isinstance(result, dict) else "<unexpected return type>"
        return answer
    if case["kind"] == "quote":
        # Compare days as numbers and each Decimal amount as a string.
        result = pricing.calculate_quote(Decimal(data["daily_rate"]), data["days"], data["driver_age"], data["gps"], data["insurance"])
        return {key: getattr(result, key) if key == "days" else str(getattr(result, key)) for key in case["expected"]}
    if case["kind"] == "refund":
        return str(pricing.calculate_refund(Decimal(data["total"]), data["hours"]))
    if case["kind"] == "hours":
        return pricing.hours_until_pickup(date.fromisoformat(data["pickup"]), datetime.fromisoformat(data["now"]))
    if case["kind"] == "money":
        return str(pricing.money(Decimal(data["value"])))
    raise ValueError("Unknown case kind")


def differences(case, actual):
    # An empty dictionary means the test passed. Otherwise it shows what differed.
    # Compare the expected fields and keep the other returned values as evidence.
    expected = case["expected"]
    if isinstance(expected, dict):
        return {key: dict(expected=value, actual=actual.get(key)) for key, value in expected.items() if actual.get(key) != value}
    if case["kind"] == "hours":
        # Dividing minutes by 60 can give a repeating decimal, so allow a tiny difference.
        # This applies to hours only. Money values must still match exactly.
        return {} if abs(actual - expected) < 1e-9 else dict(expected=expected, actual=actual)
    return {} if actual == expected else dict(expected=expected, actual=actual)
