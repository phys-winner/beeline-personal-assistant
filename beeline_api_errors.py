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
    def __init__(self, value, response):
        self.value = value
        self.response = response

    def __str__(self):
        return str(self.value) + ' ' + str(self.response)

    def __repr__(self):
        return repr(self.value) + ' ' + repr(self.response)

