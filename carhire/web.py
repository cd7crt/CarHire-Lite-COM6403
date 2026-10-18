"""HTML pages for customers and staff."""
from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from . import clock, repository, services
from .exceptions import (
    InvalidTransitionError,
    NotFoundError,
    UnavailableError,
    ValidationError,
)

web_bp = Blueprint("web", __name__)


@web_bp.app_errorhandler(404)
def page_not_found(_error):
    return render_template("404.html"), 404


@web_bp.errorhandler(NotFoundError)
def handle_not_found(exc):
    return render_template("404.html", message=str(exc)), 404


# ----------------------------------------------------------------- cars ----

@web_bp.get("/")
def index():
    query = request.args.get("q", "").strip()
    cars = repository.search_cars(query) if query else repository.list_cars()
    return render_template("index.html", cars=cars, query=query)


@web_bp.route("/cars/<int:car_id>/book", methods=["GET", "POST"])
def book(car_id):
    car = repository.get_car(car_id)
    if car is None:
        abort(404)

    form, errors, status = {}, {}, 200
    if request.method == "POST":
        form = request.form.to_dict()
        try:
            booking = services.create_booking({**form, "car_id": car_id}, clock.now())
        except ValidationError as exc:
            errors, status = exc.errors, 400
        except UnavailableError as exc:
            errors, status = {"form": str(exc)}, 409
        else:
            flash(f"Booking confirmed. Your reference is {booking['reference']}.", "success")
            return redirect(url_for("web.booking_detail", reference=booking["reference"]))

    return render_template("book.html", car=car, form=form, errors=errors), status


# ------------------------------------------------------------- bookings ----

@web_bp.get("/bookings")
def bookings():
    return render_template("bookings.html", bookings=services.list_bookings())


@web_bp.get("/bookings/find")
def find_booking():
    reference = request.args.get("reference", "").strip()
    if reference:
        try:
            booking = services.get_booking(reference)
        except NotFoundError:
            flash(f"No booking found with reference {reference}.", "error")
        else:
            return redirect(url_for("web.booking_detail", reference=booking["reference"]))
    return render_template("find.html", reference=reference)


@web_bp.get("/bookings/<reference>")
def booking_detail(reference):
    booking = services.get_booking(reference)
    return render_template("booking.html", booking=booking)


@web_bp.post("/bookings/<reference>/cancel")
def cancel(reference):
    try:
        booking = services.cancel_booking(reference, clock.now())
    except InvalidTransitionError as exc:
        flash(str(exc), "error")
    else:
        flash(f"Booking cancelled. Refund due: £{booking['refund_amount']}.", "success")
    return redirect(url_for("web.booking_detail", reference=reference))


@web_bp.post("/bookings/<reference>/pickup")
def pick_up(reference):
    try:
        services.pick_up(reference)
    except InvalidTransitionError as exc:
        flash(str(exc), "error")
    else:
        flash("Pick-up recorded.", "success")
    return redirect(url_for("web.booking_detail", reference=reference))


@web_bp.post("/bookings/<reference>/return")
def return_car(reference):
    try:
        booking = services.return_car(reference, request.form.get("actual_return_date"))
    except (InvalidTransitionError, ValidationError) as exc:
        flash(str(exc), "error")
    else:
        flash(f"Return recorded. Late fee: £{booking['late_fee']}.", "success")
    return redirect(url_for("web.booking_detail", reference=reference))
