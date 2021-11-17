import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.models.account_type import USER_ID
from aurweb.models.package_base import PackageBase
from aurweb.models.package_comment import PackageComment
from aurweb.models.user import User

user = pkgbase = None


@pytest.fixture(autouse=True)
def setup(db_test):
    global user, pkgbase

    with db.begin():
        user = db.create(User, Username="test", Email="test@example.org",
                         RealName="Test User", Passwd="testPassword",
                         AccountTypeID=USER_ID)
        pkgbase = db.create(PackageBase, Name="test-package", Maintainer=user)


def test_package_comment_creation():
    with db.begin():
        package_comment = db.create(PackageComment, PackageBase=pkgbase,
                                    User=user, Comments="Test comment.",
                                    RenderedComment="Test rendered comment.")
    assert bool(package_comment.ID)


def test_package_comment_null_package_base_raises_exception():
    with pytest.raises(IntegrityError):
        PackageComment(User=user, Comments="Test comment.",
                       RenderedComment="Test rendered comment.")


def test_package_comment_null_user_raises_exception():
    with pytest.raises(IntegrityError):
        PackageComment(PackageBase=pkgbase,
                       Comments="Test comment.",
                       RenderedComment="Test rendered comment.")


def test_package_comment_null_comments_raises_exception():
    with pytest.raises(IntegrityError):
        PackageComment(PackageBase=pkgbase, User=user,
                       RenderedComment="Test rendered comment.")


def test_package_comment_null_renderedcomment_defaults():
    with db.begin():
        record = db.create(PackageComment, PackageBase=pkgbase,
                           User=user, Comments="Test comment.")
    assert record.RenderedComment == str()
