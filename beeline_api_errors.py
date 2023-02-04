class TokenExpired(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return repr('TokenExpired')


class StatusNotOK(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class InvalidResponse(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

