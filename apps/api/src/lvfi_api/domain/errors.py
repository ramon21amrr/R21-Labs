"""Small, explicit error vocabulary for the backend foundation."""


class PersistenceUnavailableError(RuntimeError):
    """Raised when a required persistence dependency cannot serve a request."""
