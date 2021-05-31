from sqlalchemy.orm import mapper

from aurweb.db import make_relationship
from aurweb.models.package_base import PackageBase
from aurweb.schema import PackageKeywords


class PackageKeyword:
    def __init__(self,
                 PackageBase: PackageBase = None,
                 Keyword: str = None):
        self.PackageBase = PackageBase
        self.Keyword = Keyword


mapper(PackageKeyword, PackageKeywords, properties={
    "PackageBase": make_relationship(PackageBase,
                                     PackageKeywords.c.PackageBaseID,
                                     "keywords")
})
