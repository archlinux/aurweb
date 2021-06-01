from sqlalchemy.orm import mapper

from aurweb.schema import Licenses


class License:
    def __init__(self, Name: str = None):
        self.Name = Name


mapper(License, Licenses)
