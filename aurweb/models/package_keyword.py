from sqlalchemy.orm import mapper
from sqlalchemy.exc import IntegrityError

from aurweb.db import make_relationship
from aurweb.models.package_base import PackageBase
from aurweb.schema import PackageKeywords


class PackageKeyword:
    def __init__(self,
                 PackageBase: PackageBase = None,
                 Keyword: str = None):
        self.PackageBase = PackageBase
        if not self.PackageBase:
            raise IntegrityError(
                statement="Primary key PackageBaseID cannot be null.",
                orig="PackageKeywords.PackageBaseID",
                params=("NULL"))

        self.Keyword = Keyword


mapper(PackageKeyword, PackageKeywords, properties={
    "PackageBase": make_relationship(PackageBase,
                                     PackageKeywords.c.PackageBaseID,
                                     "keywords")
})
