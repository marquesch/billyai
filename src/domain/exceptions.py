class ResourceNotFoundException(Exception):
    pass


class UserNotFoundException(ResourceNotFoundException):
    pass


class CategoryNotFoundException(ResourceNotFoundException):
    pass


class BillNotFoundException(ResourceNotFoundException):
    pass


class KeyNotFoundException(ResourceNotFoundException):
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


class CategoryAlreadyExistsException(Exception):
    pass
