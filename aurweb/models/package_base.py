from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import mapper

from aurweb.db import make_relationship
from aurweb.models.user import User
from aurweb.schema import PackageBases


class PackageBase:
    def __init__(self, Name: str = None, Flagger: User = None,
                 Maintainer: User = None, Submitter: User = None,
                 Packager: User = None, **kwargs):
        self.Name = Name
        if not self.Name:
            raise IntegrityError(
                statement="Column Name cannot be null.",
                orig="PackageBases.Name",
                params=("NULL"))

        self.Flagger = Flagger
        self.Maintainer = Maintainer
        self.Submitter = Submitter
        self.Packager = Packager

        self.NumVotes = kwargs.get("NumVotes")
        self.Popularity = kwargs.get("Popularity")
        self.OutOfDateTS = kwargs.get("OutOfDateTS")
        self.FlaggerComment = kwargs.get("FlaggerComment", str())
        self.SubmittedTS = kwargs.get("SubmittedTS",
                                      datetime.utcnow().timestamp())
        self.ModifiedTS = kwargs.get("ModifiedTS",
                                     datetime.utcnow().timestamp())


mapper(PackageBase, PackageBases, properties={
    "Flagger": make_relationship(User, PackageBases.c.FlaggerUID,
                                 "flagged_bases"),
    "Submitter": make_relationship(User, PackageBases.c.SubmitterUID,
                                   "submitted_bases"),
    "Maintainer": make_relationship(User, PackageBases.c.MaintainerUID,
                                    "maintained_bases"),
    "Packager": make_relationship(User, PackageBases.c.PackagerUID,
                                  "package_bases")
})
