"""Small, explicit error vocabulary for the backend foundation."""


class PersistenceUnavailableError(RuntimeError):
    """Raised when a required persistence dependency cannot serve a request."""


class ResourceNotFoundError(LookupError):
    """Raised when a requested public resource does not exist."""


class StatisticsNotFoundError(LookupError):
    """Raised when an existing match has no normalized statistics."""


class InvalidQueryError(ValueError):
    """Raised when a query uses an unsupported or inconsistent filter."""
