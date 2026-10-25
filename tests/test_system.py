import pytest
import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the Flask application
try:
    from carhire import app
except ImportError:
    from run import app


# Create a test client for the application
@pytest.fixture
def client():
    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client


# TC07: Test a successful car booking
def test_tc07_happy_path(client):
    today = datetime.now()

    offset = random.randint(1000, 4000)
    pickup_date = (today + timedelta(days=offset)).strftime('%Y-%m-%d')
    return_date = (today + timedelta(days=offset + 3)).strftime('%Y-%m-%d')

    response = client.post('/cars/1/book', data={
        'customer_name': 'William Dassoler',
        'customer_email': 'william.dassoler@test.co.uk',
        'driver_age': '30',
        'licence_number': 'DASSO920123AB1CD',
        'pickup_date': pickup_date,
        'return_date': return_date
    }, follow_redirects=True)

    html = response.data.decode('utf-8')

    assert response.status_code == 200
    assert 'CONFIRMED' in html


# TC08: Test that a driver under the minimum age is rejected
def test_tc08_age_restriction(client):
    today = datetime.now()

    offset = random.randint(5000, 7000)
    pickup_date = (today + timedelta(days=offset)).strftime('%Y-%m-%d')
    return_date = (today + timedelta(days=offset + 3)).strftime('%Y-%m-%d')

    response = client.post('/cars/1/book', data={
        'customer_name': 'Sahra Dordete',
        'customer_email': 'sahra.dordete@test.co.uk',
        'driver_age': '17',
        'licence_number': 'DORDE920123AB1CD',
        'pickup_date': pickup_date,
        'return_date': return_date
    }, follow_redirects=True)

    html = response.data.decode('utf-8')

    assert response.status_code == 400
    assert 'data-testid="error-driver_age"' in html


# TC09: Test the discount for a long rental
def test_tc09_long_duration_discount(client):
    today = datetime.now()

    offset = random.randint(50000, 90000)
    pickup_date = (today + timedelta(days=offset)).strftime('%Y-%m-%d')
    return_date = (today + timedelta(days=offset + 18)).strftime('%Y-%m-%d')

    response = client.post('/cars/1/book', data={
        'customer_name': 'Christos',
        'customer_email': 'christos@test.co.uk',
        'driver_age': '40',
        'licence_number': 'CHRIS920123AB1CD',
        'pickup_date': pickup_date,
        'return_date': return_date
    }, follow_redirects=True)

    html = response.data.decode('utf-8')

    assert response.status_code == 200
    assert 'CONFIRMED' in html
    assert 'data-testid="price-discount"' in html