class ResourceNotFoundException(Exception):
    pass


class AuthError(Exception):
    pass


class AuthorizationError(Exception):
    pass


class DecodingError(Exception):
    pass


class RegistrationError(Exception):
    pass


class PhoneNumberTakenException(RegistrationError):
    pass


class CategoryAlreadyExists(Exception):
    pass
