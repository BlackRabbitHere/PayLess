from payment_scraper.core.enums import ErrorCode


class ScraperError(Exception):
    def __init__(self, code: ErrorCode, message: str, *, retryable: bool = False, result=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.result = result
