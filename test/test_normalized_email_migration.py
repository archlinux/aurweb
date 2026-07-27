import sqlalchemy as sa

from migrations.versions import (
    b7c419f0a2d1_add_normalizedemail_to_user as migration,
)

metadata = sa.MetaData()

# Hand-rolled because aurweb.schema's Users already carries the index this
# migration creates.
users = sa.Table(
    "Users",
    metadata,
    sa.Column("ID", sa.Integer, primary_key=True),
    sa.Column("Username", sa.String(32), nullable=False),
    sa.Column("Email", sa.String(254), nullable=False),
    sa.Column("EmailVerified", sa.Integer, nullable=False),
    sa.Column("Suspended", sa.Integer, nullable=False),
    sa.Column("NormalizedEmail", sa.String(320)),
)

package_bases = sa.Table(
    "PackageBases",
    metadata,
    sa.Column("ID", sa.Integer, primary_key=True),
    sa.Column("MaintainerUID", sa.Integer),
    sa.Column("SubmitterUID", sa.Integer),
    sa.Column("PackagerUID", sa.Integer),
    sa.Column("FlaggerUID", sa.Integer),
)

package_comments = sa.Table(
    "PackageComments",
    metadata,
    sa.Column("ID", sa.Integer, primary_key=True),
    sa.Column("UsersID", sa.Integer),
    sa.Column("EditedUsersID", sa.Integer),
    sa.Column("DelUsersID", sa.Integer),
)

package_votes = sa.Table(
    "PackageVotes",
    metadata,
    sa.Column("UsersID", sa.Integer, primary_key=True),
)

package_comaintainers = sa.Table(
    "PackageComaintainers",
    metadata,
    sa.Column("UsersID", sa.Integer, primary_key=True),
)

package_requests = sa.Table(
    "PackageRequests",
    metadata,
    sa.Column("ID", sa.Integer, primary_key=True),
    sa.Column("UsersID", sa.Integer),
    sa.Column("ClosedUID", sa.Integer),
)

package_notifications = sa.Table(
    "PackageNotifications",
    metadata,
    sa.Column("UserID", sa.Integer, primary_key=True),
)

ssh_pubkeys = sa.Table(
    "SSHPubKeys",
    metadata,
    sa.Column("UserID", sa.Integer, primary_key=True),
)

vote_info = sa.Table(
    "VoteInfo",
    metadata,
    sa.Column("ID", sa.Integer, primary_key=True),
    sa.Column("SubmitterID", sa.Integer),
)

votes = sa.Table(
    "Votes",
    metadata,
    sa.Column("UserID", sa.Integer, primary_key=True),
)


def make_conn():
    engine = sa.create_engine("sqlite://")
    metadata.create_all(engine)
    return engine.begin()


def user(uid: int, email: str, normalized: str | None = "", **kwargs) -> dict:
    return {
        "ID": uid,
        "Username": f"user{uid}",
        "Email": email,
        "EmailVerified": 0,
        "Suspended": 0,
        "NormalizedEmail": email.lower() if normalized == "" else normalized,
        **kwargs,
    }


def normalized_emails(conn) -> list[tuple]:
    return conn.execute(
        sa.select(users.c.ID, users.c.NormalizedEmail).order_by(users.c.ID)
    ).all()


def assert_index_would_hold(rows: list[tuple]) -> None:
    kept = [normalized for _, normalized in rows if normalized is not None]
    assert len(kept) == len(set(kept))


def test_null_duplicates_prefers_active_legitimate_canonical_oldest() -> None:
    with make_conn() as conn:
        conn.execute(
            users.insert(),
            [
                # ID 1 owns the canonical literal but is suspended.
                user(1, "alias@gmail.com", "alias@gmail.com", Suspended=1),
                user(2, "a.lias+x@gmail.com", "alias@gmail.com", EmailVerified=1),
                # ID 3 owns the literal but ID 4 is the verified one.
                user(3, "second@gmail.com", "second@gmail.com"),
                user(4, "second+x@gmail.com", "second@gmail.com", EmailVerified=1),
                # The canonical literal decides, and it belongs to the higher ID.
                user(5, "third+x@gmail.com", "third@gmail.com", EmailVerified=1),
                user(6, "Third@GMail.com", "third@gmail.com", EmailVerified=1),
                # Nothing else separates these, so the oldest wins.
                user(7, "fourth+a@gmail.com", "fourth@gmail.com", EmailVerified=1),
                user(8, "fourth+b@gmail.com", "fourth@gmail.com", EmailVerified=1),
                # Both are verified, so only Suspended can decide.
                user(
                    9,
                    "fifth@gmail.com",
                    "fifth@gmail.com",
                    EmailVerified=1,
                    Suspended=1,
                ),
                user(10, "fifth+x@gmail.com", "fifth@gmail.com", EmailVerified=1),
                user(11, "unique@example.com"),
            ],
        )

        migration._null_duplicates(conn)
        rows = normalized_emails(conn)

    assert rows == [
        (1, None),
        (2, "alias@gmail.com"),
        (3, None),
        (4, "second@gmail.com"),
        (5, None),
        (6, "third@gmail.com"),
        (7, "fourth@gmail.com"),
        (8, None),
        (9, None),
        (10, "fifth@gmail.com"),
        (11, "unique@example.com"),
    ]
    assert_index_would_hold(rows)


def test_null_duplicates_keeps_suspended_member_that_owns_the_group() -> None:
    with make_conn() as conn:
        conn.execute(
            users.insert(),
            [
                user(1, "alias@gmail.com", "alias@gmail.com", Suspended=1),
                user(2, "alias+x@gmail.com", "alias@gmail.com", Suspended=1),
            ],
        )
        conn.execute(package_votes.insert(), [{"UsersID": 2}])

        migration._null_duplicates(conn)
        rows = normalized_emails(conn)

    assert rows == [(1, None), (2, "alias@gmail.com")]


def test_null_duplicates_keeps_group_with_content_only() -> None:
    with make_conn() as conn:
        conn.execute(
            users.insert(),
            [
                user(1, "alias@gmail.com", "alias@gmail.com"),
                user(2, "alias+tag@gmail.com", "alias@gmail.com"),
            ],
        )
        conn.execute(package_votes.insert(), [{"UsersID": 2}])

        migration._null_duplicates(conn)
        rows = normalized_emails(conn)

    assert rows == [(1, None), (2, "alias@gmail.com")]


def test_null_duplicates_clears_unverified_group_without_content() -> None:
    with make_conn() as conn:
        conn.execute(
            users.insert(),
            [
                user(1, "alias@gmail.com", "alias@gmail.com"),
                user(2, "alias+tag@gmail.com", "alias@gmail.com"),
            ],
        )

        migration._null_duplicates(conn)
        rows = normalized_emails(conn)

    assert rows == [(1, None), (2, None)]
