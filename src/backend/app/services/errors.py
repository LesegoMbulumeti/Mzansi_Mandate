class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


class ValidationError(Exception):
    pass


class IntegrationError(Exception):
    def __init__(self, message: str, outcome_unknown: bool = False):
        super().__init__(message)
        self.outcome_unknown = outcome_unknown
