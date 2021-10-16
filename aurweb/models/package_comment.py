from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

from aurweb.models.declarative import Base
from aurweb.models.package_base import PackageBase as _PackageBase
from aurweb.models.user import User as _User


class PackageComment(Base):
    __tablename__ = "PackageComments"

    ID = Column(Integer, primary_key=True)

    PackageBaseID = Column(
        Integer, ForeignKey("PackageBases.ID", ondelete="CASCADE"),
        nullable=False)
    PackageBase = relationship(
        _PackageBase, backref=backref("comments", lazy="dynamic",
                                      cascade="all,delete"),
        foreign_keys=[PackageBaseID])

    UsersID = Column(Integer, ForeignKey("Users.ID", ondelete="SET NULL"))
    User = relationship(
        _User, backref=backref("package_comments", lazy="dynamic"),
        foreign_keys=[UsersID])

    EditedUsersID = Column(
        Integer, ForeignKey("Users.ID", ondelete="SET NULL"))
    Editor = relationship(
        _User, backref=backref("edited_comments", lazy="dynamic"),
        foreign_keys=[EditedUsersID])

    DelUsersID = Column(
        Integer, ForeignKey("Users.ID", ondelete="SET NULL"))
    Deleter = relationship(
        _User, backref=backref("deleted_comments", lazy="dynamic"),
        foreign_keys=[DelUsersID])

    __mapper_args__ = {"primary_key": [ID]}

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
