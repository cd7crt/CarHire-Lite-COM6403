import pytest
from carhire import create_app
from carhire.db import get_db, init_db

#Flask test client fixture using a shared in-memory SQLite db

@pytest.fixture
def client():
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": "file:memdb_integration?mode=memory&cache=shared",
        }
    )

    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client


def test_tc01_booking_creation_api_and_db_integration(client):
    #Check that a valid POST request to /api/bookings 
    #correctly calls services.py,
    ##saves the booking in the SQLite database 
    # using repository.py and returns status 201.
    
    payload = {
        "car_id": 2,
        "customer_name": "Jay Zikhali",
        "customer_email": "jay.zikhali@swe.com",
        "driver_age": 33,
        "licence_number": "AJNXJSNJUYRSGOYT",
        "pickup_date": "2027-02-01",
        "return_date": "2027-02-05",
        "gps": False,
        "insurance": False,
    }

    response = client.post("/api/bookings", json=payload)
    assert response.status_code == 201, (
        f"Expected 201 Created, got {response.status_code}"
    )
    data = response.get_json()
    booking_ref = data["reference"]

    with client.application.app_context():
        db = get_db()
        row = db.execute(
            "SELECT * FROM bookings WHERE reference = ?", (booking_ref,)
        ).fetchone()

        assert row is not None
        assert row["status"] == "CONFIRMED"
        assert row["customer_name"] == "Jay Zikhali"


def test_tc02_invalid_state_transition(client):
    
    #Check the system enforces the 
    # booking status lifecycle rules by making sure
    #that a cancelled booking cannot be updated to picked up or returned.

    payload = {
        "car_id": 1,
        "customer_name": "Victor Afuye",
        "customer_email": "info@victorafuye.com",
        "driver_age": 25,
        "licence_number": "VICTORA200456034",
        "pickup_date": "2027-02-10",
        "return_date": "2027-02-12",
        "gps": False,
        "insurance": False,
    }
    res = client.post("/api/bookings", json=payload)
    assert res.status_code == 201
    booking_reference = res.get_json()["reference"]

    cancel_res = client.post(f"/api/bookings/{booking_reference}/cancel")
    assert cancel_res.status_code == 200

    return_res = client.post(
        f"/api/bookings/{booking_reference}/return",
        json={"actual_return_date": "2027-02-12"},
    )


    assert return_res.status_code in [400, 409], (
        f"Expected HTTP 400 or 409 for illegal state transition, but got HTTP {return_res.status_code}"
    )