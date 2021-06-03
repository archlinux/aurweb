from sqlalchemy.orm import mapper

from aurweb.schema import ApiRateLimit as _ApiRateLimit


class ApiRateLimit:
    def __init__(self, IP: str = None,
                 Requests: int = None,
                 WindowStart: int = None):
        self.IP = IP
        self.Requests = Requests
        self.WindowStart = WindowStart


mapper(ApiRateLimit, _ApiRateLimit, primary_key=[_ApiRateLimit.c.IP])
