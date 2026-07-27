"""Small, explicit error vocabulary for the backend foundation."""


class PersistenceUnavailableError(RuntimeError):
    """Raised when a required persistence dependency cannot serve a request."""


class ResourceNotFoundError(LookupError):
    """Raised when a requested public resource does not exist."""


class StatisticsNotFoundError(LookupError):
    """Raised when an existing match has no normalized statistics."""


class InvalidQueryError(ValueError):
    """Raised when a query uses an unsupported or inconsistent filter."""


class MethodOneSampleIncompleteError(ValueError):
    """Raised before execution when APP-005 did not find both complete series."""


class MethodOneSampleInvalidError(ValueError):
    """Raised before execution when a required deterministic observation is invalid."""


class MethodOneEngineError(RuntimeError):
    """Raised when the public Pricing Engine facade cannot produce a final payload."""
