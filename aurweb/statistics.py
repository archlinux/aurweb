from sqlalchemy import func

from aurweb import config, db, time
from aurweb.cache import db_count_cache, db_query_cache
from aurweb.models import PackageBase, PackageRequest, RequestType, User
from aurweb.models.account_type import (
    PACKAGE_MAINTAINER_AND_DEV_ID,
    PACKAGE_MAINTAINER_ID,
    USER_ID,
)
from aurweb.models.package_request import (
    ACCEPTED_ID,
    CLOSED_ID,
    PENDING_ID,
    REJECTED_ID,
)
from aurweb.prometheus import PACKAGES, REQUESTS, USERS

cache_expire = config.getint("cache", "expiry_time_statistics", 300)

HOMEPAGE_COUNTERS = [
    "package_count",
    "orphan_count",
    "seven_days_old_added",
    "seven_days_old_updated",
    "year_old_updated",
    "never_updated",
    "user_count",
    "package_maintainer_count",
]
REQUEST_COUNTERS = [
    "total_requests",
    "pending_requests",
    "closed_requests",
    "accepted_requests",
    "rejected_requests",
]
PROMETHEUS_USER_COUNTERS = [
    ("package_maintainer_count", "package_maintainer"),
    ("regular_user_count", "user"),
]
PROMETHEUS_PACKAGE_COUNTERS = [
    ("orphan_count", "orphan"),
    ("never_updated", "not_updated"),
    ("updated_packages", "updated"),
]


class Statistics:
    seven_days = 86400 * 7
    one_hour = 3600
    year = seven_days * 52

    def __init__(self, cache_expire: int | None = None) -> None:
        self.expiry_time = cache_expire
        self.now = time.utcnow()
        self.seven_days_ago = self.now - self.seven_days
        self.year_ago = self.now - self.year

        self.user_query = db.query(User)
        self.bases_query = db.query(PackageBase)
        self.updated_query = db.query(PackageBase).filter(
            PackageBase.ModifiedTS - PackageBase.SubmittedTS >= self.one_hour
        )
        self.request_query = db.query(PackageRequest)

    def get_count(self, counter: str) -> int:  # noqa: C901
        query = None
        match counter:
            # Packages
            case "package_count":
                query = self.bases_query
            case "orphan_count":
                query = self.bases_query.filter(PackageBase.MaintainerUID.is_(None))
            case "seven_days_old_added":
                query = self.bases_query.filter(
                    PackageBase.SubmittedTS >= self.seven_days_ago
                )
            case "seven_days_old_updated":
                query = self.updated_query.filter(
                    PackageBase.ModifiedTS >= self.seven_days_ago
                )
            case "year_old_updated":
                query = self.updated_query.filter(
                    PackageBase.ModifiedTS >= self.year_ago
                )
            case "never_updated":
                query = self.bases_query.filter(
                    PackageBase.ModifiedTS - PackageBase.SubmittedTS < self.one_hour
                )
            case "updated_packages":
                query = self.bases_query.filter(
                    PackageBase.ModifiedTS - PackageBase.SubmittedTS > self.one_hour,
                    ~PackageBase.MaintainerUID.is_(None),
                )
            # Users
            case "user_count":
                query = self.user_query
            case "package_maintainer_count":
                query = self.user_query.filter(
                    User.AccountTypeID.in_(
                        (
                            PACKAGE_MAINTAINER_ID,
                            PACKAGE_MAINTAINER_AND_DEV_ID,
                        )
                    )
                )
            case "regular_user_count":
                query = self.user_query.filter(User.AccountTypeID == USER_ID)

            # Requests
            case "total_requests":
                query = self.request_query
            case "pending_requests":
                query = self.request_query.filter(PackageRequest.Status == PENDING_ID)
            case "closed_requests":
                query = self.request_query.filter(PackageRequest.Status == CLOSED_ID)
            case "accepted_requests":
                query = self.request_query.filter(PackageRequest.Status == ACCEPTED_ID)
            case "rejected_requests":
                query = self.request_query.filter(PackageRequest.Status == REJECTED_ID)
            case _:
                return -1

        return db_count_cache(counter, query, expire=self.expiry_time)


def update_prometheus_metrics() -> None:
    stats = Statistics(cache_expire)
    # Users gauge
    for counter, utype in PROMETHEUS_USER_COUNTERS:
        count = stats.get_count(counter)
        USERS.labels(utype).set(count)

    # Packages gauge
    for counter, state in PROMETHEUS_PACKAGE_COUNTERS:
        count = stats.get_count(counter)
        PACKAGES.labels(state).set(count)

    # Requests gauge
    query = (
        db.get_session()
        .query(PackageRequest, func.count(PackageRequest.ID), RequestType.Name)
        .join(RequestType)
        .group_by(RequestType.Name, PackageRequest.Status)
    )
    results = db_query_cache("request_metrics", query, cache_expire)
    for record in results:
        status = record[0].status_display()
        count = record[1]
        rtype = record[2]
        REQUESTS.labels(type=rtype, status=status).set(count)


def _get_counts(counters: list[str]) -> dict[str, int]:
    stats = Statistics(cache_expire)
    result = {}
    for counter in counters:
        result[counter] = stats.get_count(counter)

    return result


def get_homepage_counts() -> dict[str, int]:
    return _get_counts(HOMEPAGE_COUNTERS)


def get_request_counts() -> dict[str, int]:
    return _get_counts(REQUEST_COUNTERS)
