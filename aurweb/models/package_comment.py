from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb import schema
from aurweb.models.declarative import Base
from aurweb.models.package_base import PackageBase as _PackageBase
from aurweb.models.user import User as _User


class PackageComment(Base):
    __table__ = schema.PackageComments
    __tablename__ = __table__.name
    __mapper_args__ = {"primary_key": [__table__.c.ID]}

    PackageBase = relationship(
        _PackageBase, backref=backref("comments", lazy="dynamic",
                                      cascade="all, delete"),
        foreign_keys=[__table__.c.PackageBaseID])

    User = relationship(
        _User, backref=backref("package_comments", lazy="dynamic"),
        foreign_keys=[__table__.c.UsersID])

    Editor = relationship(
        _User, backref=backref("edited_comments", lazy="dynamic"),
        foreign_keys=[__table__.c.EditedUsersID])

    Deleter = relationship(
        _User, backref=backref("deleted_comments", lazy="dynamic"),
        foreign_keys=[__table__.c.DelUsersID])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.PackageBase and not self.PackageBaseID:
            raise IntegrityError(
                statement="Foreign key PackageBaseID cannot be null.",
                orig="PackageComments.PackageBaseID",
                params=("NULL"))

        if not self.User and not self.UsersID:
            raise IntegrityError(
                statement="Foreign key UsersID cannot be null.",
                orig="PackageComments.UsersID",
                params=("NULL"))

        if self.Comments is None:
            raise IntegrityError(
                statement="Column Comments cannot be null.",
                orig="PackageComments.Comments",
                params=("NULL"))

        if self.RenderedComment is None:
            self.RenderedComment = str()

    def maintainers(self):
        return list(filter(
            lambda e: e is not None,
            [self.PackageBase.Maintainer] + [
                c.User for c in self.PackageBase.comaintainers
            ]
        ))
