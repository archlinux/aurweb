from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import mapper

from aurweb.schema import ApiRateLimit as _ApiRateLimit


class ApiRateLimit:
    def __init__(self, IP: str = None,
                 Requests: int = None,
                 WindowStart: int = None):
        self.IP = IP

        self.Requests = Requests
        if self.Requests is None:
            raise IntegrityError(
                statement="Column Requests cannot be null.",
                orig="ApiRateLimit.Requests",
                params=("NULL"))

        self.WindowStart = WindowStart
        if self.WindowStart is None:
            raise IntegrityError(
                statement="Column WindowStart cannot be null.",
                orig="ApiRateLimit.WindowStart",
                params=("NULL"))


mapper(ApiRateLimit, _ApiRateLimit, primary_key=[_ApiRateLimit.c.IP])
