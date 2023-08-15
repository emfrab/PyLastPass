class LastPassException(Exception):
    pass


class WrongCredentialsException(LastPassException):
    pass


class UserNotLoggedInException(LastPassException):
    pass
