from aurweb import config, db, time
from aurweb.cache import db_count_cache
from aurweb.models import PackageBase, User
from aurweb.models.account_type import TRUSTED_USER_AND_DEV_ID, TRUSTED_USER_ID, USER_ID
from aurweb.prometheus import PACKAGES, USERS


class Statistics:
    HOMEPAGE_COUNTERS = [
        "package_count",
        "orphan_count",
        "seven_days_old_added",
        "seven_days_old_updated",
        "year_old_updated",
        "never_updated",
        "user_count",
        "trusted_user_count",
    ]
    PROMETHEUS_USER_COUNTERS = [
        ("trusted_user_count", "tu"),
        ("regular_user_count", "user"),
    ]
    PROMETHEUS_PACKAGE_COUNTERS = [
        ("orphan_count", "orphan"),
        ("never_updated", "not_updated"),
        ("updated_packages", "updated"),
    ]

    seven_days = 86400 * 7
    one_hour = 3600
    year = seven_days * 52

    def __init__(self, cache_expire: int = None) -> "Statistics":
        self.expiry_time = cache_expire
        self.now = time.utcnow()
        self.seven_days_ago = self.now - self.seven_days
        self.year_ago = self.now - self.year
        self.user_query = db.query(User)
        self.bases_query = db.query(PackageBase)
        self.updated_query = db.query(PackageBase).filter(
            PackageBase.ModifiedTS - PackageBase.SubmittedTS >= self.one_hour
        )

    def get_count(self, counter: str) -> int:
        query = None
        match counter:
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
            case "user_count":
                query = self.user_query
            case "trusted_user_count":
                query = self.user_query.filter(
                    User.AccountTypeID.in_(
                        (
                            TRUSTED_USER_ID,
                            TRUSTED_USER_AND_DEV_ID,
                        )
                    )
                )
            case "regular_user_count":
                query = self.user_query.filter(User.AccountTypeID == USER_ID)
            case _:
                return -1

        return db_count_cache(counter, query, expire=self.expiry_time)


def update_prometheus_metrics():
    cache_expire = config.getint("cache", "expiry_time")
    stats = Statistics(cache_expire)
    # Users gauge
    for counter, utype in stats.PROMETHEUS_USER_COUNTERS:
        count = stats.get_count(counter)
        USERS.labels(utype).set(count)

    # Packages gauge
    for counter, state in stats.PROMETHEUS_PACKAGE_COUNTERS:
        count = stats.get_count(counter)
        PACKAGES.labels(state).set(count)
