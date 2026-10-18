"""JSON API. All endpoints are under /api."""
from flask import Blueprint, jsonify, request

from . import clock, repository, services
from .exceptions import (
    InvalidTransitionError,
    NotFoundError,
    UnavailableError,
    ValidationError,
)

api_bp = Blueprint("api", __name__)


def _json_body():
    """Request body as a dict; an empty dict if the body is missing or not JSON."""
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else {}


# ------------------------------------------------------- error handling ----

@api_bp.errorhandler(ValidationError)
def handle_validation_error(exc):
    return jsonify({"errors": exc.errors}), 400


@api_bp.errorhandler(NotFoundError)
def handle_not_found(exc):
    return jsonify({"error": str(exc)}), 404


@api_bp.errorhandler(UnavailableError)
@api_bp.errorhandler(InvalidTransitionError)
def handle_conflict(exc):
    return jsonify({"error": str(exc)}), 409


# ------------------------------------------------------------ endpoints ----

@api_bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@api_bp.get("/cars")
def list_cars():
    make = request.args.get("make", "").strip()
    cars = repository.search_cars(make) if make else repository.list_cars()
    return jsonify([services.car_to_dict(car) for car in cars])


@api_bp.get("/cars/<int:car_id>")
def get_car(car_id):
    car = repository.get_car(car_id)
    if car is None:
        raise NotFoundError(f"Car {car_id} does not exist.")
    return jsonify(services.car_to_dict(car))


@api_bp.post("/quote")
def quote():
    car, result = services.get_quote(_json_body(), clock.now().date())
    return jsonify({"car": services.car_to_dict(car), "quote": result.as_dict()})


@api_bp.get("/bookings")
def list_bookings():
    return jsonify([services.booking_to_dict(b) for b in services.list_bookings()])


@api_bp.post("/bookings")
def create_booking():
    booking = services.create_booking(_json_body(), clock.now())
    return jsonify(services.booking_to_dict(booking)), 201


@api_bp.get("/bookings/<reference>")
def get_booking(reference):
    return jsonify(services.booking_to_dict(services.get_booking(reference)))


@api_bp.post("/bookings/<reference>/cancel")
def cancel_booking(reference):
    booking = services.cancel_booking(reference, clock.now())
    return jsonify(services.booking_to_dict(booking))


@api_bp.post("/bookings/<reference>/pickup")
def pick_up(reference):
    return jsonify(services.booking_to_dict(services.pick_up(reference)))


@api_bp.post("/bookings/<reference>/return")
def return_car(reference):
    body = _json_body()
    booking = services.return_car(reference, body.get("actual_return_date"))
    return jsonify(services.booking_to_dict(booking))
