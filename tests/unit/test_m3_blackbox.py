"""Run the full set of test cases with pytest."""
import pytest
from m3_blackbox_cases import CASES, observe, differences


# Run each input row and show its test ID in the results.
@pytest.mark.parametrize("case", CASES, ids=[case["row_id"] for case in CASES])
def test_specification(case):
    # Run the app with these inputs and compare the result with the requirements.
    actual = observe(case)
    mismatch = differences(case, actual)
    # If the results differ, show the row ID, rule and values that did not match.
    assert not mismatch, f"{case['row_id']} {case['requirements']}: {mismatch}"
