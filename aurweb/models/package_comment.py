from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import backref, relationship

import aurweb.models.package_base
import aurweb.models.user

from aurweb.models.declarative import Base


class PackageComment(Base):
    __tablename__ = "PackageComments"

    ID = Column(Integer, primary_key=True)

    PackageBaseID = Column(
        Integer, ForeignKey("PackageBases.ID", ondelete="CASCADE"),
        nullable=False)
    PackageBase = relationship(
        "PackageBase", backref=backref("comments", lazy="dynamic"),
        foreign_keys=[PackageBaseID])

    UsersID = Column(Integer, ForeignKey("Users.ID", ondelete="SET NULL"))
    User = relationship(
        "User", backref=backref("package_comments", lazy="dynamic"),
        foreign_keys=[UsersID])

    EditedUsersID = Column(
        Integer, ForeignKey("Users.ID", ondelete="SET NULL"))
    Editor = relationship(
        "User", backref=backref("edited_comments", lazy="dynamic"),
        foreign_keys=[EditedUsersID])

    DelUsersID = Column(
        Integer, ForeignKey("Users.ID", ondelete="SET NULL"))
    Deleter = relationship(
        "User", backref=backref("deleted_comments", lazy="dynamic"),
        foreign_keys=[DelUsersID])

    __mapper_args__ = {"primary_key": [ID]}

    def __init__(self,
                 PackageBase: aurweb.models.package_base.PackageBase = None,
                 User: aurweb.models.user.User = None,
                 **kwargs):
        super().__init__(**kwargs)

        self.PackageBase = PackageBase
        if not self.PackageBase:
            raise IntegrityError(
                statement="Foreign key PackageBaseID cannot be null.",
                orig="PackageComments.PackageBaseID",
                params=("NULL"))

        self.User = User
        if not self.User:
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
