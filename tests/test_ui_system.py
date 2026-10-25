import random
from datetime import datetime, timedelta

import random
from datetime import datetime, timedelta
import urllib.request
import pytest

pytest.importorskip("pytest_playwright")
try:
    urllib.request.urlopen("http://127.0.0.1:5000", timeout=1)
except OSError:
    pytest.skip("UI tests need the app running: python run.py", allow_module_level=True)

from playwright.sync_api import Page, expect
BASE_URL = "http://127.0.0.1:5000"

def test_tc07_happy_path_ui(page: Page):
    today = datetime.now()
    offset = random.randint(1000, 4000)
    pickup = (today + timedelta(days=offset)).strftime('%Y-%m-%d')
    return_date = (today + timedelta(days=offset + 3)).strftime('%Y-%m-%d')

    page.goto(f"{BASE_URL}/cars/1/book")
    page.fill("input[name='customer_name']", "William Dassoler")
    page.fill("input[name='customer_email']", "william.dassoler@test.co.uk")
    page.fill("input[name='driver_age']", "30")
    page.fill("input[name='licence_number']", "DASSO920123AB1CD")
    page.fill("input[name='pickup_date']", pickup)
    page.fill("input[name='return_date']", return_date)
    page.click("button[type='submit']")

    # Capture a screenshot of the success screen and save it to the directory
    page.screenshot(path="evidence_tc07_pass.png")
    expect(page.locator("body")).to_contain_text("CONFIRMED")


def test_tc08_underage_driver_ui(page: Page):
    today = datetime.now()
    offset = random.randint(5000, 7000)
    pickup = (today + timedelta(days=offset)).strftime('%Y-%m-%d')
    return_date = (today + timedelta(days=offset + 3)).strftime('%Y-%m-%d')

    page.goto(f"{BASE_URL}/cars/1/book")
    page.fill("input[name='customer_name']", "Sahra Dordete")
    page.fill("input[name='customer_email']", "sahra.dordete@test.co.uk")
    page.fill("input[name='driver_age']", "17")
    page.fill("input[name='licence_number']", "DORDE920123AB1CD")
    page.fill("input[name='pickup_date']", pickup)
    page.fill("input[name='return_date']", return_date)
    page.click("button[type='submit']")

    page.screenshot(path="evidence_tc08_fail.png")
    expect(page.locator("[data-testid='error-driver_age']")).to_be_visible()


def test_tc09_long_duration_discount_ui(page: Page):
    today = datetime.now()
    offset = random.randint(50000, 90000)
    pickup = (today + timedelta(days=offset)).strftime('%Y-%m-%d')
    return_date = (today + timedelta(days=offset + 18)).strftime('%Y-%m-%d')

    page.goto(f"{BASE_URL}/cars/1/book")
    page.fill("input[name='customer_name']", "Christos")
    page.fill("input[name='customer_email']", "christos@test.co.uk")
    page.fill("input[name='driver_age']", "40")
    page.fill("input[name='licence_number']", "CHRIS920123AB1CD")
    page.fill("input[name='pickup_date']", pickup)
    page.fill("input[name='return_date']", return_date)
    page.click("button[type='submit']")

    page.screenshot(path="evidence_tc09_discount.png")
    expect(page.locator("body")).to_contain_text("CONFIRMED")
    expect(page.locator("[data-testid='price-discount']")).to_be_visible()