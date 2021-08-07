from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

import aurweb.models.package_base
import aurweb.models.request_type
import aurweb.models.user

from aurweb.models.declarative import Base

PENDING = "Pending"
CLOSED = "Closed"
ACCEPTED = "Accepted"
REJECTED = "Rejected"

# Integer values used for the Status column of PackageRequest.
PENDING_ID = 0
CLOSED_ID = 1
ACCEPTED_ID = 2
REJECTED_ID = 3


class PackageRequest(Base):
    __tablename__ = "PackageRequests"

    ID = Column(Integer, primary_key=True)

    ReqTypeID = Column(
        Integer, ForeignKey("RequestTypes.ID", ondelete="NO ACTION"),
        nullable=False)
    RequestType = relationship(
        "RequestType", backref=backref("package_requests", lazy="dynamic"),
        foreign_keys=[ReqTypeID])

    UsersID = Column(Integer, ForeignKey("Users.ID", ondelete="SET NULL"))
    User = relationship(
        "User", backref=backref("package_requests", lazy="dynamic"),
        foreign_keys=[UsersID])

    PackageBaseID = Column(
        Integer, ForeignKey("PackageBases.ID", ondelete="SET NULL"),
        nullable=False)
    PackageBase = relationship(
        "PackageBase", backref=backref("requests", lazy="dynamic"),
        foreign_keys=[PackageBaseID])

    ClosedUID = Column(Integer, ForeignKey("Users.ID", ondelete="SET NULL"))
    Closer = relationship(
        "User", backref=backref("closed_requests", lazy="dynamic"),
        foreign_keys=[ClosedUID])

    __mapper_args__ = {"primary_key": [ID]}

    STATUS_DISPLAY = {
        PENDING_ID: PENDING,
        CLOSED_ID: CLOSED,
        ACCEPTED_ID: ACCEPTED,
        REJECTED_ID: REJECTED
    }

    def __init__(self,
                 RequestType: aurweb.models.request_type.RequestType = None,
                 PackageBase: aurweb.models.package_base.PackageBase = None,
                 PackageBaseName: str = None,
                 User: aurweb.models.user.User = None,
                 Comments: str = None,
                 ClosureComment: str = None,
                 **kwargs):
        super().__init__(**kwargs)

        self.RequestType = RequestType
        if not self.RequestType:
            raise IntegrityError(
                statement="Foreign key ReqTypeID cannot be null.",
                orig="PackageRequests.ReqTypeID",
                params=("NULL"))

        self.PackageBase = PackageBase
        if not self.PackageBase:
            raise IntegrityError(
                statement="Foreign key PackageBaseID cannot be null.",
                orig="PackageRequests.PackageBaseID",
                params=("NULL"))

        self.PackageBaseName = PackageBaseName
        if not self.PackageBaseName:
            raise IntegrityError(
                statement="Column PackageBaseName cannot be null.",
                orig="PackageRequests.PackageBaseName",
                params=("NULL"))

        self.User = User
        if not self.User:
            raise IntegrityError(
                statement="Foreign key UsersID cannot be null.",
                orig="PackageRequests.UsersID",
                params=("NULL"))

        self.Comments = Comments
        if self.Comments is None:
            raise IntegrityError(
                statement="Column Comments cannot be null.",
                orig="PackageRequests.Comments",
                params=("NULL"))

        self.ClosureComment = ClosureComment
        if self.ClosureComment is None:
            raise IntegrityError(
                statement="Column ClosureComment cannot be null.",
                orig="PackageRequests.ClosureComment",
                params=("NULL"))

    def status_display(self) -> str:
        """ Return a display string for the Status column. """
        return self.STATUS_DISPLAY[self.Status]
