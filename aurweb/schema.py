"""
Schema of aurweb's database.

Changes here should always be accompanied by an Alembic migration, which can be
usually be automatically generated. See `migrations/README` for details.
"""

from sqlalchemy import (
    TIMESTAMP,
    Column,
    ForeignKey,
    Index,
    MetaData,
    String,
    Table,
    Text,
    event,
    text,
)
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, INTEGER, NUMERIC, SMALLINT
from sqlalchemy.ext.compiler import compiles

import aurweb.config

# from sqlalchemy import event


db_backend = aurweb.config.get("database", "backend")


@compiles(SMALLINT, "sqlite")
def compile_smallint_sqlite(type_, compiler, **kw):  # pragma: no cover
    """SMALLINT is not supported on SQLite. Substitute it with INTEGER."""
    return "INTEGER"


@compiles(BIGINT, "sqlite")
def compile_bigint_sqlite(type_, compiler, **kw):  # pragma: no cover
    """
    For SQLite's AUTOINCREMENT to work on BIGINT columns, we need to map BIGINT
    to INTEGER. Aside from that, BIGINT is the same as INTEGER for SQLite.

    See https://docs.sqlalchemy.org/en/13/dialects/sqlite.html#allowing-autoincrement-behavior-sqlalchemy-types-other-than-integer-integer
    """  # noqa: E501
    return "INTEGER"


@event.listens_for(Column, "before_parent_attach")
def attach_column(column: Column, parent, **kw):
    column.origname = column.name
    column.name = column.name.lower()


@event.listens_for(Index, "before_parent_attach")
def attach_index(index, parent, **kw):
    index.name = index.name.lower()


metadata = MetaData()

# Define the Account Types for the AUR.
AccountTypes = Table(
    "AccountTypes",
    metadata,
    Column("ID", SMALLINT(), primary_key=True),
    Column("AccountType", String(32), nullable=False, server_default=text("''")),
    quote=False,
)


# User information for each user regardless of type.
Users = Table(
    "Users",
    metadata,
    Column("ID", INTEGER(), primary_key=True),
    Column(
        "AccountTypeID",
        ForeignKey("AccountTypes.ID", ondelete="NO ACTION"),
        nullable=False,
        server_default=text("1"),
    ),
    Column("Suspended", BOOLEAN(), nullable=False, server_default=text("False")),
    Column("Username", String(32), nullable=False, unique=True),
    Column("Email", String(254), nullable=False, unique=True),
    Column("BackupEmail", String(254)),
    Column("HideEmail", BOOLEAN(), nullable=False, server_default=text("False")),
    Column("Passwd", String(255), nullable=False),
    Column("Salt", String(32), nullable=False, server_default=text("''")),
    Column("ResetKey", String(32), nullable=False, server_default=text("''")),
    Column("RealName", String(64), nullable=False, server_default=text("''")),
    Column("LangPreference", String(6), nullable=False, server_default=text("'en'")),
    Column("Timezone", String(32), nullable=False, server_default=text("'UTC'")),
    Column("Homepage", Text),
    Column("IRCNick", String(32), nullable=False, server_default=text("''")),
    Column("PGPKey", String(40)),
    Column("LastLogin", BIGINT(), nullable=False, server_default=text("0")),
    Column("LastLoginIPAddress", String(45)),
    Column("LastSSHLogin", BIGINT(), nullable=False, server_default=text("0")),
    Column("LastSSHLoginIPAddress", String(45)),
    Column("InactivityTS", BIGINT(), nullable=False, server_default=text("0")),
    Column(
        "RegistrationTS",
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
    Column("CommentNotify", BOOLEAN(), nullable=False, server_default=text("True")),
    Column("UpdateNotify", BOOLEAN(), nullable=False, server_default=text("False")),
    Column("OwnershipNotify", BOOLEAN(), nullable=False, server_default=text("True")),
    Column("SSOAccountID", String(255), nullable=True, unique=True),
    Index("UsersAccountTypeID", "AccountTypeID"),
    Column(
        "HideDeletedComments",
        BOOLEAN(),
        nullable=False,
        server_default=text("False"),
    ),
    Index("UsernameLowerUnique", text("lower(username)"), unique=True),
    Index("EmailLowerUnique", text("lower(email)"), unique=True),
    quote=False,
)


# SSH public keys used for the aurweb SSH/Git interface.
SSHPubKeys = Table(
    "SSHPubKeys",
    metadata,
    Column("UserID", ForeignKey("Users.ID", ondelete="CASCADE"), nullable=False),
    Column("Fingerprint", String(44), primary_key=True),
    Column("PubKey", String(4096), nullable=False),
    quote=False,
)


# Track Users logging in/out of AUR web site.
Sessions = Table(
    "Sessions",
    metadata,
    Column("UsersID", ForeignKey("Users.ID", ondelete="CASCADE"), nullable=False),
    Column("SessionID", String(32), nullable=False, unique=True),
    Column("LastUpdateTS", BIGINT(), nullable=False),
    quote=False,
)


# Information on package bases
PackageBases = Table(
    "PackageBases",
    metadata,
    Column("ID", INTEGER(), primary_key=True),
    Column("Name", String(255), nullable=False, unique=True),
    Column("NumVotes", INTEGER(), nullable=False, server_default=text("0")),
    Column(
        "Popularity",
        NUMERIC(10, 6) if db_backend == "postgres" else String(17),
        nullable=False,
        server_default=text("0"),
    ),
    Column(
        "PopularityUpdated",
        TIMESTAMP,
        nullable=False,
        server_default=text("'1970-01-01 00:00:01.000000'"),
    ),
    Column("OutOfDateTS", BIGINT()),
    Column("FlaggerComment", Text, nullable=False),
    Column("SubmittedTS", BIGINT(), nullable=False),
    Column("ModifiedTS", BIGINT(), nullable=False),
    Column(
        "FlaggerUID", ForeignKey("Users.ID", ondelete="SET NULL")
    ),  # who flagged the package out-of-date?
    # deleting a user will cause packages to be orphaned, not deleted
    Column(
        "SubmitterUID", ForeignKey("Users.ID", ondelete="SET NULL")
    ),  # who submitted it?
    Column("MaintainerUID", ForeignKey("Users.ID", ondelete="SET NULL")),  # User
    Column("PackagerUID", ForeignKey("Users.ID", ondelete="SET NULL")),  # Last packager
    Index("BasesMaintainerUID", "MaintainerUID"),
    Index("BasesNumVotes", "NumVotes"),
    Index("BasesPackagerUID", "PackagerUID"),
    Index("BasesSubmitterUID", "SubmitterUID"),
    Index("BasesSubmittedTS", "SubmittedTS"),
    Index("BasesModifiedTS", "ModifiedTS"),
    Index("BasesNameLowerUnique", text("lower(name)"), unique=True),
    quote=False,
)


# Keywords of package bases
PackageKeywords = Table(
    "PackageKeywords",
    metadata,
    Column(
        "PackageBaseID",
        ForeignKey("PackageBases.ID", ondelete="CASCADE"),
        primary_key=True,
        nullable=True,
    ),
    Column(
        "Keyword",
        String(255),
        primary_key=True,
        nullable=False,
        server_default=text("''"),
    ),
    Index("KeywordsPackageBaseID", "PackageBaseID"),
    quote=False,
)


# Information about the actual packages
Packages = Table(
    "Packages",
    metadata,
    Column("ID", INTEGER(), primary_key=True),
    Column(
        "PackageBaseID",
        ForeignKey("PackageBases.ID", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("Name", String(255), nullable=False, unique=True),
    Column("Version", String(255), nullable=False, server_default=text("''")),
    Column("Description", String(255)),
    Column("URL", String(8000)),
    Index("PackagesNameLowerUnique", text("lower(name)"), unique=True),
    quote=False,
)


# Information about licenses
Licenses = Table(
    "Licenses",
    metadata,
    Column("ID", INTEGER(), primary_key=True),
    Column("Name", String(255), nullable=False, unique=True),
    quote=False,
)


# Information about package-license-relations
PackageLicenses = Table(
    "PackageLicenses",
    metadata,
    Column(
        "PackageID",
        ForeignKey("Packages.ID", ondelete="CASCADE"),
        primary_key=True,
        nullable=True,
    ),
    Column(
        "LicenseID",
        ForeignKey("Licenses.ID", ondelete="CASCADE"),
        primary_key=True,
        nullable=True,
    ),
    quote=False,
)


# Information about groups
Groups = Table(
    "Groups",
    metadata,
    Column("ID", INTEGER(), primary_key=True),
    Column("Name", String(255), nullable=False, unique=True),
    quote=False,
)


# Information about package-group-relations
PackageGroups = Table(
    "PackageGroups",
    metadata,
    Column(
        "PackageID",
        ForeignKey("Packages.ID", ondelete="CASCADE"),
        primary_key=True,
        nullable=True,
    ),
    Column(
        "GroupID",
        ForeignKey("Groups.ID", ondelete="CASCADE"),
        primary_key=True,
        nullable=True,
    ),
    quote=False,
)


# Define the package dependency types
DependencyTypes = Table(
    "DependencyTypes",
    metadata,
    Column("ID", SMALLINT(), primary_key=True),
    Column("Name", String(32), nullable=False, server_default=text("''")),
    quote=False,
)


# Track which dependencies a package has
PackageDepends = Table(
    "PackageDepends",
    metadata,
    Column("PackageID", ForeignKey("Packages.ID", ondelete="CASCADE"), nullable=False),
    Column(
        "DepTypeID",
        ForeignKey("DependencyTypes.ID", ondelete="NO ACTION"),
        nullable=False,
    ),
    Column("DepName", String(255), nullable=False),
    Column("DepDesc", String(255)),
    Column("DepCondition", String(255)),
    Column("DepArch", String(255)),
    Index("DependsDepName", "DepName"),
    Index("DependsPackageID", "PackageID"),
    quote=False,
)


# Define the package relation types
RelationTypes = Table(
    "RelationTypes",
    metadata,
    Column("ID", SMALLINT(), primary_key=True),
    Column("Name", String(32), nullable=False, server_default=text("''")),
    quote=False,
)


# Track which conflicts, provides and replaces a package has
PackageRelations = Table(
    "PackageRelations",
    metadata,
    Column("PackageID", ForeignKey("Packages.ID", ondelete="CASCADE"), nullable=False),
    Column(
        "RelTypeID",
        ForeignKey("RelationTypes.ID", ondelete="NO ACTION"),
        nullable=False,
    ),
    Column("RelName", String(255), nullable=False),
    Column("RelCondition", String(255)),
    Column("RelArch", String(255)),
    Index("RelationsPackageID", "PackageID"),
    Index("RelationsRelName", "RelName"),
    quote=False,
)


# Track which sources a package has
PackageSources = Table(
    "PackageSources",
    metadata,
    Column("PackageID", ForeignKey("Packages.ID", ondelete="CASCADE"), nullable=False),
    Column("Source", String(8000), nullable=False, server_default=text("'/dev/null'")),
    Column("SourceArch", String(255)),
    Index("SourcesPackageID", "PackageID"),
    quote=False,
)


# Track votes for packages
PackageVotes = Table(
    "PackageVotes",
    metadata,
    Column("UsersID", ForeignKey("Users.ID", ondelete="CASCADE"), nullable=False),
    Column(
        "PackageBaseID",
        ForeignKey("PackageBases.ID", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("VoteTS", BIGINT(), nullable=False),
    Index("VoteUsersIDPackageID", "UsersID", "PackageBaseID", unique=True),
    Index("VotesPackageBaseID", "PackageBaseID"),
    Index("VotesUsersID", "UsersID"),
    quote=False,
)


# Record comments for packages
PackageComments = Table(
    "PackageComments",
    metadata,
    Column("ID", BIGINT(), primary_key=True),
    Column(
        "PackageBaseID",
        ForeignKey("PackageBases.ID", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("UsersID", ForeignKey("Users.ID", ondelete="SET NULL")),
    Column("Comments", Text, nullable=False),
    Column("RenderedComment", Text, nullable=False),
    Column("CommentTS", BIGINT(), nullable=False, server_default=text("0")),
    Column("EditedTS", BIGINT()),
    Column("EditedUsersID", ForeignKey("Users.ID", ondelete="SET NULL")),
    Column("DelTS", BIGINT()),
    Column("DelUsersID", ForeignKey("Users.ID", ondelete="CASCADE")),
    Column("PinnedTS", BIGINT(), nullable=False, server_default=text("0")),
    Index("CommentsPackageBaseID", "PackageBaseID"),
    Index("CommentsUsersID", "UsersID"),
    quote=False,
)


# Package base co-maintainers
PackageComaintainers = Table(
    "PackageComaintainers",
    metadata,
    Column("UsersID", ForeignKey("Users.ID", ondelete="CASCADE"), nullable=False),
    Column(
        "PackageBaseID",
        ForeignKey("PackageBases.ID", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("Priority", INTEGER(), nullable=False),
    Index("ComaintainersPackageBaseID", "PackageBaseID"),
    Index("ComaintainersUsersID", "UsersID"),
    quote=False,
)


# Package base notifications
PackageNotifications = Table(
    "PackageNotifications",
    metadata,
    Column(
        "PackageBaseID",
        ForeignKey("PackageBases.ID", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("UserID", ForeignKey("Users.ID", ondelete="CASCADE"), nullable=False),
    Index("NotifyUserIDPkgID", "UserID", "PackageBaseID", unique=True),
    quote=False,
)


# Package name blacklist
PackageBlacklist = Table(
    "PackageBlacklist",
    metadata,
    Column("ID", INTEGER(), primary_key=True),
    Column("Name", String(64), nullable=False, unique=True),
    quote=False,
)


# Providers in the official repositories
OfficialProviders = Table(
    "OfficialProviders",
    metadata,
    Column("ID", INTEGER(), primary_key=True),
    Column("Name", String(64), nullable=False),
    Column("Repo", String(64), nullable=False),
    Column("Provides", String(64), nullable=False),
    Index("ProviderNameProvides", "Name", "Provides", unique=True),
    quote=False,
)


# Define package request types
RequestTypes = Table(
    "RequestTypes",
    metadata,
    Column("ID", SMALLINT(), primary_key=True),
    Column("Name", String(32), nullable=False, server_default=text("''")),
    quote=False,
)


# Package requests
PackageRequests = Table(
    "PackageRequests",
    metadata,
    Column("ID", BIGINT(), primary_key=True),
    Column(
        "ReqTypeID", ForeignKey("RequestTypes.ID", ondelete="NO ACTION"), nullable=False
    ),
    Column("PackageBaseID", ForeignKey("PackageBases.ID", ondelete="SET NULL")),
    Column("PackageBaseName", String(255), nullable=False),
    Column("MergeBaseName", String(255)),
    Column("UsersID", ForeignKey("Users.ID", ondelete="SET NULL")),
    Column("Comments", Text, nullable=False),
    Column("ClosureComment", Text, nullable=False),
    Column("RequestTS", BIGINT(), nullable=False, server_default=text("0")),
    Column("ClosedTS", BIGINT()),
    Column("ClosedUID", ForeignKey("Users.ID", ondelete="SET NULL")),
    Column("Status", SMALLINT(), nullable=False, server_default=text("0")),
    Index("RequestsPackageBaseID", "PackageBaseID"),
    Index("RequestsUsersID", "UsersID"),
    quote=False,
)


# Vote information
VoteInfo = Table(
    "VoteInfo",
    metadata,
    Column("ID", INTEGER(), primary_key=True),
    Column("Agenda", Text, nullable=False),
    Column("User", String(32), nullable=False),
    Column("Submitted", BIGINT(), nullable=False),
    Column("End", BIGINT(), nullable=False),
    Column(
        "Quorum",
        NUMERIC(2, 2) if db_backend == "postgres" else String(5),
        nullable=False,
    ),
    Column("SubmitterID", ForeignKey("Users.ID", ondelete="CASCADE"), nullable=False),
    Column("Yes", INTEGER(), nullable=False, server_default=text("'0'")),
    Column("No", INTEGER(), nullable=False, server_default=text("'0'")),
    Column("Abstain", INTEGER(), nullable=False, server_default=text("'0'")),
    Column(
        "ActiveUsers",
        INTEGER(),
        nullable=False,
        server_default=text("'0'"),
    ),
    quote=False,
)


# Individual vote records
Votes = Table(
    "Votes",
    metadata,
    Column("VoteID", ForeignKey("VoteInfo.ID", ondelete="CASCADE"), nullable=False),
    Column("UserID", ForeignKey("Users.ID", ondelete="CASCADE"), nullable=False),
    quote=False,
)


# Malicious user banning
Bans = Table(
    "Bans",
    metadata,
    Column("IPAddress", String(45), primary_key=True),
    Column("BanTS", TIMESTAMP, nullable=False),
    quote=False,
)


# Terms and Conditions
Terms = Table(
    "Terms",
    metadata,
    Column("ID", INTEGER(), primary_key=True),
    Column("Description", String(255), nullable=False),
    Column("URL", String(8000), nullable=False),
    Column("Revision", INTEGER(), nullable=False, server_default=text("1")),
    quote=False,
)


# Terms and Conditions accepted by users
AcceptedTerms = Table(
    "AcceptedTerms",
    metadata,
    Column("UsersID", ForeignKey("Users.ID", ondelete="CASCADE"), nullable=False),
    Column("TermsID", ForeignKey("Terms.ID", ondelete="CASCADE"), nullable=False),
    Column("Revision", INTEGER(), nullable=False, server_default=text("0")),
    quote=False,
)


# Rate limits for API
ApiRateLimit = Table(
    "ApiRateLimit",
    metadata,
    Column("IP", String(45), primary_key=True, unique=True, default=str()),
    Column("Requests", INTEGER(), nullable=False),
    Column("WindowStart", BIGINT(), nullable=False),
    Index("ApiRateLimitWindowStart", "WindowStart"),
    quote=False,
)
