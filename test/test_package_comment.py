import pytest

from sqlalchemy.exc import IntegrityError

from aurweb.db import begin, create, query, rollback
from aurweb.models.account_type import AccountType
from aurweb.models.package_base import PackageBase
from aurweb.models.package_comment import PackageComment
from aurweb.models.user import User
from aurweb.testing import setup_test_db

user = pkgbase = None


@pytest.fixture(autouse=True)
def setup():
    setup_test_db("PackageBases", "PackageComments", "Users")

    global user, pkgbase

    account_type = query(AccountType,
                         AccountType.AccountType == "User").first()
    with begin():
        user = create(User, Username="test", Email="test@example.org",
                      RealName="Test User", Passwd="testPassword",
                      AccountType=account_type)
        pkgbase = create(PackageBase, Name="test-package", Maintainer=user)


def test_package_comment_creation():
    with begin():
        package_comment = create(PackageComment,
                                 PackageBase=pkgbase,
                                 User=user,
                                 Comments="Test comment.",
                                 RenderedComment="Test rendered comment.")
    assert bool(package_comment.ID)


def test_package_comment_null_package_base_raises_exception():
    with pytest.raises(IntegrityError):
        with begin():
            create(PackageComment, User=user, Comments="Test comment.",
                   RenderedComment="Test rendered comment.")
    rollback()


def test_package_comment_null_user_raises_exception():
    with pytest.raises(IntegrityError):
        with begin():
            create(PackageComment, PackageBase=pkgbase,
                   Comments="Test comment.",
                   RenderedComment="Test rendered comment.")
    rollback()


def test_package_comment_null_comments_raises_exception():
    with pytest.raises(IntegrityError):
        with begin():
            create(PackageComment, PackageBase=pkgbase, User=user,
                   RenderedComment="Test rendered comment.")
    rollback()


def test_package_comment_null_renderedcomment_defaults():
    with begin():
        record = create(PackageComment,
                        PackageBase=pkgbase,
                        User=user,
                        Comments="Test comment.")
    assert record.RenderedComment == str()
