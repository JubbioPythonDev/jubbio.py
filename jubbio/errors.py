class JubbioException(Exception):
    pass


class HTTPException(JubbioException):
    def __init__(self, response, message=None):
        self.response = response
        self.status = response.status
        self.code = 0

        if isinstance(message, dict):
            self.code = message.get("code", 0)
            self.text = message.get("message", "")
        else:
            self.text = message or ""

        fmt = f"{self.status} {self.response.reason}"
        if self.text:
            fmt += f": {self.text}"
        if self.code:
            fmt += f" (error code: {self.code})"

        super().__init__(fmt)


class Forbidden(HTTPException):
    pass


class NotFound(HTTPException):
    pass


class RateLimited(HTTPException):
    def __init__(self, response, message=None):
        super().__init__(response, message)
        self.retry_after = 0.0
        if isinstance(message, dict):
            self.retry_after = message.get("retry_after", 0.0)


class LoginFailure(JubbioException):
    pass


class GatewayError(JubbioException):
    def __init__(self, message=None, code=None):
        self.code = code
        super().__init__(message or f"Gateway hatası (kod: {code})")


class InvalidToken(LoginFailure):
    pass


class InvalidArgument(JubbioException):
    pass
