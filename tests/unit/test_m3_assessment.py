"""Run the four M3 report cases and check each input row."""
import pytest
from m3_blackbox_cases import CASES, observe, differences


def rows(*ids, kind=None):
    return [case for case in CASES if case["case_id"] in ids
            and (kind is None or case["kind"] == kind)]


AGE = rows("UTB-01")
PRICE = rows("UTB-02", "UTB-08")
REFUND = rows("UTB-09", kind="refund")
ROUNDING = rows("UTB-10")
REPORT_CASES = {"UTB-01": AGE, "UTB-02": PRICE,
                "UTB-09": REFUND, "UTB-10": ROUNDING}


def check(case):
    actual = observe(case)
    mismatch = differences(case, actual)
    assert not mismatch, f"{case['row_id']}: {mismatch}"


@pytest.mark.parametrize("case", AGE, ids=lambda case: case["row_id"])
def test_utb01_age_eligibility(case):
    # Check the age limits for both car categories and try invalid age inputs.
    check(case)


@pytest.mark.parametrize("case", PRICE, ids=lambda case: case["row_id"])
def test_utb02_price_components(case):
    # Check the worked example, then the 16 combinations in the decision table.
    # Check each part of the price to see where a wrong total comes from.
    check(case)


@pytest.mark.parametrize("case", REFUND, ids=lambda case: case["row_id"])
def test_utb09_refund_boundaries(case):
    # At exactly 48 hours the refund should be full. At 24 hours it should be half.
    check(case)


@pytest.mark.parametrize("case", ROUNDING, ids=lambda case: case["row_id"])
def test_utb10_money_rounding(case):
    # Convert strings to Decimal so the rounding inputs stay exact.
    check(case)
