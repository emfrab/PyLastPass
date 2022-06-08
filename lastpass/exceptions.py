class LastPassException(Exception):
    pass


class WrongCredentialsException(LastPassException):
    pass
