class TimezoneRetrievalError(Exception):
    """Exception raised when a timezone cannot be retrieved from an entry."""

    def __init__(self, location, message="Unable to retrieve timezone from the entry"):
        self.location = location
        self.message = message
        super().__init__(f"{message}: {location}")
