"""Custom application exceptions."""


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(self.message)


# Authentication exceptions
class PhoneAlreadyExistsException(AppException):
    def __init__(self):
        super().__init__(
            message="Phone number already registered",
            code="PHONE_ALREADY_EXISTS"
        )


class InvalidCredentialsException(AppException):
    def __init__(self):
        super().__init__(
            message="Invalid phone number or password",
            code="INVALID_CREDENTIALS"
        )


class AccountDeactivatedException(AppException):
    def __init__(self):
        super().__init__(
            message="Account has been deactivated",
            code="ACCOUNT_DEACTIVATED"
        )


class InvalidTokenException(AppException):
    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message=message, code="INVALID_TOKEN")


class TokenExpiredException(AppException):
    def __init__(self):
        super().__init__(
            message="Token has expired",
            code="TOKEN_EXPIRED"
        )


class PasswordTooWeakException(AppException):
    def __init__(self, message: str = "Password does not meet requirements"):
        super().__init__(message=message, code="PASSWORD_TOO_WEAK")


class UserNotFoundException(AppException):
    def __init__(self):
        super().__init__(
            message="User not found",
            code="USER_NOT_FOUND"
        )


class RateLimitExceededException(AppException):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(
            message=f"Too many attempts. Try again in {retry_after} seconds",
            code="RATE_LIMIT_EXCEEDED"
        )


# Authorization exceptions
class PermissionDeniedException(AppException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, code="PERMISSION_DENIED")
