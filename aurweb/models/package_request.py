from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb import schema
from aurweb.models.declarative import Base
from aurweb.models.package_base import PackageBase as _PackageBase
from aurweb.models.request_type import RequestType as _RequestType
from aurweb.models.user import User as _User

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
    __table__ = schema.PackageRequests
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.ID]}

    RequestType = relationship(
        _RequestType,
        backref=backref("package_requests", lazy="dynamic"),
        foreign_keys=[__table__.c.ReqTypeID],
    )

    User = relationship(
        _User,
        backref=backref("package_requests", lazy="dynamic"),
        foreign_keys=[__table__.c.UsersID],
    )

    PackageBase = relationship(
        _PackageBase,
        backref=backref("requests", lazy="dynamic"),
        foreign_keys=[__table__.c.PackageBaseID],
    )

    Closer = relationship(
        _User,
        backref=backref("closed_requests", lazy="dynamic"),
        foreign_keys=[__table__.c.ClosedUID],
    )

    STATUS_DISPLAY = {
        PENDING_ID: PENDING,
        CLOSED_ID: CLOSED,
        ACCEPTED_ID: ACCEPTED,
        REJECTED_ID: REJECTED,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.RequestType and not self.ReqTypeID:
            raise IntegrityError(
                statement="Foreign key ReqTypeID cannot be null.",
                orig="PackageRequests.ReqTypeID",
                params=("NULL"),
            )

        if not self.PackageBase and not self.PackageBaseID:
            raise IntegrityError(
                statement="Foreign key PackageBaseID cannot be null.",
                orig="PackageRequests.PackageBaseID",
                params=("NULL"),
            )

        if not self.PackageBaseName:
            raise IntegrityError(
                statement="Column PackageBaseName cannot be null.",
                orig="PackageRequests.PackageBaseName",
                params=("NULL"),
            )

        if not self.User and not self.UsersID:
            raise IntegrityError(
                statement="Foreign key UsersID cannot be null.",
                orig="PackageRequests.UsersID",
                params=("NULL"),
            )

        if self.Comments is None:
            raise IntegrityError(
                statement="Column Comments cannot be null.",
                orig="PackageRequests.Comments",
                params=("NULL"),
            )

        if self.ClosureComment is None:
            raise IntegrityError(
                statement="Column ClosureComment cannot be null.",
                orig="PackageRequests.ClosureComment",
                params=("NULL"),
            )

    def status_display(self) -> str:
        """Return a display string for the Status column."""
        return self.STATUS_DISPLAY[self.Status]
