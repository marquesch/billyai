class ResourceNotFoundException(Exception):
    pass


class AuthenticationError(Exception):
    pass


class AuthorizationError(Exception):
    pass


class DecodingError(Exception):
    pass


class RegistrationError(Exception):
    pass


class PhoneNumberTakenException(RegistrationError):
    pass
