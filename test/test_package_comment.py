from typing import Generator

import pytest
from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.account_type import USER_ID
from aurweb.models.package_base import PackageBase
from aurweb.models.package_comment import PackageComment
from aurweb.models.user import User


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture
def user() -> Generator[User]:
    with db.begin():
        user = db.create(
            User,
            Username="test",
            Email="test@example.org",
            RealName="Test User",
            Passwd="testPassword",
            AccountTypeID=USER_ID,
        )
    yield user


@pytest.fixture
def pkgbase(user: User) -> Generator[PackageBase]:
    with db.begin():
        pkgbase = db.create(PackageBase, Name="test-package", Maintainer=user)
    yield pkgbase


def test_package_comment_creation(user: User, pkgbase: PackageBase):
    with db.begin():
        package_comment = db.create(
            PackageComment,
            PackageBase=pkgbase,
            User=user,
            Comments="Test comment.",
            RenderedComment="Test rendered comment.",
        )
    assert bool(package_comment.ID)


def test_package_comment_null_pkgbase_raises(user: User):
    with pytest.raises(IntegrityError):
        PackageComment(
            User=user,
            Comments="Test comment.",
            RenderedComment="Test rendered comment.",
        )


def test_package_comment_null_user_raises(pkgbase: PackageBase):
    with pytest.raises(IntegrityError):
        PackageComment(
            PackageBase=pkgbase,
            Comments="Test comment.",
            RenderedComment="Test rendered comment.",
        )


def test_package_comment_null_comments_raises(user: User, pkgbase: PackageBase):
    with pytest.raises(IntegrityError):
        PackageComment(
            PackageBase=pkgbase, User=user, RenderedComment="Test rendered comment."
        )


def test_package_comment_null_renderedcomment_defaults(
    user: User, pkgbase: PackageBase
):
    with db.begin():
        record = db.create(
            PackageComment, PackageBase=pkgbase, User=user, Comments="Test comment."
        )
    assert record.RenderedComment == str()
