import aurweb.db

from aurweb import models


def setup_test_db(*args):
    """ This function is to be used to setup a test database before
    using it. It takes a variable number of table strings, and for
    each table in that set of table strings, it deletes all records.

    The primary goal of this method is to configure empty tables
    that tests can use from scratch. This means that tests using
    this function should make sure they do not depend on external
    records and keep their logic self-contained.

    Generally used inside of pytest fixtures, this function
    can be used anywhere, but keep in mind its functionality when
    doing so.

    Examples:
        setup_test_db("Users", "Sessions")

        test_tables = ["Users", "Sessions"];
        setup_test_db(*test_tables)
    """
    # Make sure that we've grabbed the engine before using the session.
    aurweb.db.get_engine()

    tables = list(args)
    if not tables:
        tables = [
            models.AcceptedTerm.__tablename__,
            models.ApiRateLimit.__tablename__,
            models.Ban.__tablename__,
            models.Group.__tablename__,
            models.License.__tablename__,
            models.OfficialProvider.__tablename__,
            models.Package.__tablename__,
            models.PackageBase.__tablename__,
            models.PackageBlacklist.__tablename__,
            models.PackageComaintainer.__tablename__,
            models.PackageComment.__tablename__,
            models.PackageDependency.__tablename__,
            models.PackageGroup.__tablename__,
            models.PackageKeyword.__tablename__,
            models.PackageLicense.__tablename__,
            models.PackageNotification.__tablename__,
            models.PackageRelation.__tablename__,
            models.PackageRequest.__tablename__,
            models.PackageSource.__tablename__,
            models.PackageVote.__tablename__,
            models.Session.__tablename__,
            models.SSHPubKey.__tablename__,
            models.Term.__tablename__,
            models.TUVote.__tablename__,
            models.TUVoteInfo.__tablename__,
            models.User.__tablename__,
        ]

    aurweb.db.get_session().execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in tables:
        aurweb.db.get_session().execute(f"DELETE FROM {table}")
    aurweb.db.get_session().execute("SET FOREIGN_KEY_CHECKS = 1")
    aurweb.db.get_session().expunge_all()
