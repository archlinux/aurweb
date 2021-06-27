import logging

from datetime import datetime
from http import HTTPStatus

import lxml.etree
import pytest

from fastapi.testclient import TestClient

from aurweb import db
from aurweb.asgi import app
from aurweb.models.account_type import AccountType
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.user import User
from aurweb.testing import setup_test_db

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def setup():
    setup_test_db(
        Package.__tablename__,
        PackageBase.__tablename__,
        User.__tablename__)


@pytest.fixture
def client():
    yield TestClient(app=app)


@pytest.fixture
def user():
    account_type = db.query(AccountType,
                            AccountType.AccountType == "User").first()
    yield db.create(User, Username="test",
                    Email="test@example.org",
                    RealName="Test User",
                    Passwd="testPassword",
                    AccountType=account_type)


@pytest.fixture
def packages(user):
    pkgs = []
    now = int(datetime.utcnow().timestamp())

    # Create 101 packages; we limit 100 on RSS feeds.
    for i in range(101):
        pkgbase = db.create(
            PackageBase, Maintainer=user, Name=f"test-package-{i}",
            SubmittedTS=(now + i), ModifiedTS=(now + i), autocommit=False)
        pkg = db.create(Package, Name=pkgbase.Name, PackageBase=pkgbase,
                        autocommit=False)
        pkgs.append(pkg)
    db.commit()
    yield pkgs


def parse_root(xml):
    return lxml.etree.fromstring(xml)


def test_rss(client, user, packages):
    with client as request:
        response = request.get("/rss/")
    assert response.status_code == int(HTTPStatus.OK)

    # Test that the RSS we got is sorted by descending SubmittedTS.
    def key_(pkg):
        return pkg.PackageBase.SubmittedTS
    packages = list(reversed(sorted(packages, key=key_)))

    # Just take the first 100.
    packages = packages[:100]

    root = parse_root(response.content)
    items = root.xpath("//channel/item")
    assert len(items) == 100

    for i, item in enumerate(items):
        title = next(iter(item.xpath('./title')))
        logger.debug(f"title: '{title.text}' vs name: '{packages[i].Name}'")
        assert title.text == packages[i].Name


def test_rss_modified(client, user, packages):
    with client as request:
        response = request.get("/rss/modified")
    assert response.status_code == int(HTTPStatus.OK)

    # Test that the RSS we got is sorted by descending SubmittedTS.
    def key_(pkg):
        return pkg.PackageBase.ModifiedTS
    packages = list(reversed(sorted(packages, key=key_)))

    # Just take the first 100.
    packages = packages[:100]

    root = parse_root(response.content)
    items = root.xpath("//channel/item")
    assert len(items) == 100

    for i, item in enumerate(items):
        title = next(iter(item.xpath('./title')))
        logger.debug(f"title: '{title.text}' vs name: '{packages[i].Name}'")
        assert title.text == packages[i].Name
