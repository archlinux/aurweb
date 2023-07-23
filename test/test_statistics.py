import pytest
from prometheus_client import REGISTRY, generate_latest

from aurweb import cache, db, time
from aurweb.models.account_type import TRUSTED_USER_ID, USER_ID
from aurweb.models.package import Package
from aurweb.models.package_base import PackageBase
from aurweb.models.user import User
from aurweb.statistics import Statistics, update_prometheus_metrics


@pytest.fixture(autouse=True)
def setup(db_test):
    return


@pytest.fixture(autouse=True)
def clear_fakeredis_cache():
    cache._redis.flushall()


@pytest.fixture
def test_data():
    # Create some test data (users and packages)
    with db.begin():
        for i in range(10):
            user = db.create(
                User,
                Username=f"test{i}",
                Email=f"test{i}@example.org",
                RealName=f"Test User {i}",
                Passwd="testPassword",
                AccountTypeID=USER_ID,
            )

            now = time.utcnow()
            old = now - 60 * 60 * 24 * 8  # 8 days
            older = now - 60 * 60 * 24 * 400  # 400 days

            pkgbase = db.create(
                PackageBase,
                Name=f"test-package{i}",
                Maintainer=user,
                SubmittedTS=old,
                ModifiedTS=now,
            )
            db.create(Package, PackageBase=pkgbase, Name=pkgbase.Name)

            # Modify some data to get some variances for our counters
            if i == 1:
                user.AccountTypeID = TRUSTED_USER_ID
                pkgbase.Maintainer = None
                pkgbase.SubmittedTS = now

            if i == 2:
                pkgbase.SubmittedTS = older

            if i == 3:
                pkgbase.SubmittedTS = older
                pkgbase.ModifiedTS = old
    yield


@pytest.fixture
def stats() -> Statistics:
    yield Statistics()


@pytest.mark.parametrize(
    "counter, expected",
    [
        ("package_count", 10),
        ("orphan_count", 1),
        ("seven_days_old_added", 1),
        ("seven_days_old_updated", 8),
        ("year_old_updated", 9),
        ("never_updated", 1),
        ("user_count", 10),
        ("trusted_user_count", 1),
        ("regular_user_count", 9),
        ("updated_packages", 9),
        ("nonsense", -1),
    ],
)
def test_get_count(stats: Statistics, test_data, counter: str, expected: int):
    assert stats.get_count(counter) == expected


def test_get_count_change(stats: Statistics, test_data):
    pkgs_before = stats.get_count("package_count")
    tus_before = stats.get_count("trusted_user_count")

    assert pkgs_before == 10
    assert tus_before == 1

    # Let's delete a package and promote a user to TU
    with db.begin():
        pkgbase = db.query(PackageBase).first()
        db.delete(pkgbase)

        user = db.query(User).filter(User.AccountTypeID == USER_ID).first()
        user.AccountTypeID = TRUSTED_USER_ID

    # Values should end up in (fake) redis cache so they should be the same
    assert stats.get_count("package_count") == pkgs_before
    assert stats.get_count("trusted_user_count") == tus_before

    # Let's clear the cache and check again
    cache._redis.flushall()
    assert stats.get_count("package_count") != pkgs_before
    assert stats.get_count("trusted_user_count") != tus_before


def test_update_prometheus_metrics(test_data):
    metrics = str(generate_latest(REGISTRY))

    assert "aur_users{" not in metrics
    assert "aur_packages{" not in metrics

    # Let's update our metrics. We should find our gauges now
    update_prometheus_metrics()
    metrics = str(generate_latest(REGISTRY))

    assert 'aur_users{type="user"} 9.0' in metrics
    assert 'aur_packages{state="updated"} 9.0' in metrics
