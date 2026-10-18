"""Exceptions raised by the business layer and turned into responses by the web/API layers."""


class CarHireError(Exception):
    """Base class for all expected application errors."""


class ValidationError(CarHireError):
    """Input failed validation. ``errors`` maps a field name to a message."""

    def __init__(self, errors):
        super().__init__("; ".join(errors.values()))
        self.errors = errors


class NotFoundError(CarHireError):
    """A car or booking does not exist."""


class UnavailableError(CarHireError):
    """The car is already booked for some or all of the requested dates."""


class InvalidTransitionError(CarHireError):
    """The requested status change is not allowed for this booking."""
