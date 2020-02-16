from sqlalchemy import CHAR, Column, ForeignKey, Index, MetaData, String, TIMESTAMP, Table, Text, text
from sqlalchemy.dialects.mysql import BIGINT, DECIMAL, INTEGER, TINYINT
from sqlalchemy.ext.compiler import compiles


@compiles(TINYINT, 'sqlite')
def compile_tinyint_sqlite(type_, compiler, **kw):
    """TINYINT is not supported on SQLite. Substitute it with INTEGER."""
    return 'INTEGER'


metadata = MetaData()

# Define the Account Types for the AUR.
AccountTypes = Table(
    'AccountTypes', metadata,
    Column('ID', TINYINT(unsigned=True), primary_key=True),
    Column('AccountType', String(32), nullable=False, server_default=text("''")),
    mysql_engine='InnoDB',
)


# User information for each user regardless of type.
Users = Table(
    'Users', metadata,
    Column('ID', INTEGER(unsigned=True), primary_key=True),
    Column('AccountTypeID', ForeignKey('AccountTypes.ID', ondelete="NO ACTION"), nullable=False, server_default=text("1")),
    Column('Suspended', TINYINT(unsigned=True), nullable=False, server_default=text("0")),
    Column('Username', String(32), nullable=False, unique=True),
    Column('Email', String(254), nullable=False, unique=True),
    Column('BackupEmail', String(254)),
    Column('HideEmail', TINYINT(unsigned=True), nullable=False, server_default=text("0")),
    Column('Passwd', String(255), nullable=False),
    Column('Salt', CHAR(32), nullable=False, server_default=text("''")),
    Column('ResetKey', CHAR(32), nullable=False, server_default=text("''")),
    Column('RealName', String(64), nullable=False, server_default=text("''")),
    Column('LangPreference', String(6), nullable=False, server_default=text("'en'")),
    Column('Timezone', String(32), nullable=False, server_default=text("'UTC'")),
    Column('Homepage', Text),
    Column('IRCNick', String(32), nullable=False, server_default=text("''")),
    Column('PGPKey', String(40)),
    Column('LastLogin', BIGINT(unsigned=True), nullable=False, server_default=text("0")),
    Column('LastLoginIPAddress', String(45)),
    Column('LastSSHLogin', BIGINT(unsigned=True), nullable=False, server_default=text("0")),
    Column('LastSSHLoginIPAddress', String(45)),
    Column('InactivityTS', BIGINT(unsigned=True), nullable=False, server_default=text("0")),
    Column('RegistrationTS', TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    Column('CommentNotify', TINYINT(1), nullable=False, server_default=text("1")),
    Column('UpdateNotify', TINYINT(1), nullable=False, server_default=text("0")),
    Column('OwnershipNotify', TINYINT(1), nullable=False, server_default=text("1")),
    Index('UsersAccountTypeID', 'AccountTypeID'),
    mysql_engine='InnoDB',
)


# SSH public keys used for the aurweb SSH/Git interface.
SSHPubKeys = Table(
    'SSHPubKeys', metadata,
    Column('UserID', ForeignKey('Users.ID', ondelete='CASCADE'), nullable=False),
    Column('Fingerprint', String(44), primary_key=True),
    Column('PubKey', String(4096), nullable=False),
    mysql_engine='InnoDB',
)


# Track Users logging in/out of AUR web site.
Sessions = Table(
    'Sessions', metadata,
    Column('UsersID', ForeignKey('Users.ID', ondelete='CASCADE'), nullable=False),
    Column('SessionID', CHAR(32), nullable=False, unique=True),
    Column('LastUpdateTS', BIGINT(unsigned=True), nullable=False),
    mysql_engine='InnoDB',
)


# Information on package bases
PackageBases = Table(
    'PackageBases', metadata,
    Column('ID', INTEGER(unsigned=True), primary_key=True),
    Column('Name', String(255), nullable=False, unique=True),
    Column('NumVotes', INTEGER(unsigned=True), nullable=False, server_default=text("0")),
    Column('Popularity', DECIMAL(10, 6, unsigned=True), nullable=False, server_default=text("0")),
    Column('OutOfDateTS', BIGINT(unsigned=True)),
    Column('FlaggerComment', Text, nullable=False),
    Column('SubmittedTS', BIGINT(unsigned=True), nullable=False),
    Column('ModifiedTS', BIGINT(unsigned=True), nullable=False),
    Column('FlaggerUID', ForeignKey('Users.ID', ondelete='SET NULL')),     # who flagged the package out-of-date?
    # deleting a user will cause packages to be orphaned, not deleted
    Column('SubmitterUID', ForeignKey('Users.ID', ondelete='SET NULL')),   # who submitted it?
    Column('MaintainerUID', ForeignKey('Users.ID', ondelete='SET NULL')),  # User
    Column('PackagerUID', ForeignKey('Users.ID', ondelete='SET NULL')),    # Last packager
    Index('BasesMaintainerUID', 'MaintainerUID'),
    Index('BasesNumVotes', 'NumVotes'),
    Index('BasesPackagerUID', 'PackagerUID'),
    Index('BasesSubmitterUID', 'SubmitterUID'),
    mysql_engine='InnoDB',
)


# Keywords of package bases
PackageKeywords = Table(
    'PackageKeywords', metadata,
    Column('PackageBaseID', ForeignKey('PackageBases.ID', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('Keyword', String(255), primary_key=True, nullable=False, server_default=text("''")),
    mysql_engine='InnoDB',
)


# Information about the actual packages
Packages = Table(
    'Packages', metadata,
    Column('ID', INTEGER(unsigned=True), primary_key=True),
    Column('PackageBaseID', ForeignKey('PackageBases.ID', ondelete='CASCADE'), nullable=False),
    Column('Name', String(255), nullable=False, unique=True),
    Column('Version', String(255), nullable=False, server_default=text("''")),
    Column('Description', String(255)),
    Column('URL', String(8000)),
    mysql_engine='InnoDB',
)


# Information about licenses
Licenses = Table(
    'Licenses', metadata,
    Column('ID', INTEGER(unsigned=True), primary_key=True),
    Column('Name', String(255), nullable=False, unique=True),
    mysql_engine='InnoDB',
)


# Information about package-license-relations
PackageLicenses = Table(
    'PackageLicenses', metadata,
    Column('PackageID', ForeignKey('Packages.ID', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('LicenseID', ForeignKey('Licenses.ID', ondelete='CASCADE'), primary_key=True, nullable=False),
    mysql_engine='InnoDB',
)


# Information about groups
Groups = Table(
    'Groups', metadata,
    Column('ID', INTEGER(unsigned=True), primary_key=True),
    Column('Name', String(255), nullable=False, unique=True),
    mysql_engine='InnoDB',
)


# Information about package-group-relations
PackageGroups = Table(
    'PackageGroups', metadata,
    Column('PackageID', ForeignKey('Packages.ID', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('GroupID', ForeignKey('Groups.ID', ondelete='CASCADE'), primary_key=True, nullable=False),
    mysql_engine='InnoDB',
)


# Define the package dependency types
DependencyTypes = Table(
    'DependencyTypes', metadata,
    Column('ID', TINYINT(unsigned=True), primary_key=True),
    Column('Name', String(32), nullable=False, server_default=text("''")),
    mysql_engine='InnoDB',
)


# Track which dependencies a package has
PackageDepends = Table(
    'PackageDepends', metadata,
    Column('PackageID', ForeignKey('Packages.ID', ondelete='CASCADE'), nullable=False),
    Column('DepTypeID', ForeignKey('DependencyTypes.ID', ondelete="NO ACTION"), nullable=False),
    Column('DepName', String(255), nullable=False),
    Column('DepDesc', String(255)),
    Column('DepCondition', String(255)),
    Column('DepArch', String(255)),
    Index('DependsDepName', 'DepName'),
    Index('DependsPackageID', 'PackageID'),
    mysql_engine='InnoDB',
)


# Define the package relation types
RelationTypes = Table(
    'RelationTypes', metadata,
    Column('ID', TINYINT(unsigned=True), primary_key=True),
    Column('Name', String(32), nullable=False, server_default=text("''")),
    mysql_engine='InnoDB',
)


# Track which conflicts, provides and replaces a package has
PackageRelations = Table(
    'PackageRelations', metadata,
    Column('PackageID', ForeignKey('Packages.ID', ondelete='CASCADE'), nullable=False),
    Column('RelTypeID', ForeignKey('RelationTypes.ID', ondelete="NO ACTION"), nullable=False),
    Column('RelName', String(255), nullable=False),
    Column('RelCondition', String(255)),
    Column('RelArch', String(255)),
    Index('RelationsPackageID', 'PackageID'),
    Index('RelationsRelName', 'RelName'),
    mysql_engine='InnoDB',
)


# Track which sources a package has
PackageSources = Table(
    'PackageSources', metadata,
    Column('PackageID', ForeignKey('Packages.ID', ondelete='CASCADE'), nullable=False),
    Column('Source', String(8000), nullable=False, server_default=text("'/dev/null'")),
    Column('SourceArch', String(255)),
    Index('SourcesPackageID', 'PackageID'),
    mysql_engine='InnoDB',
)


# Track votes for packages
PackageVotes = Table(
    'PackageVotes', metadata,
    Column('UsersID', ForeignKey('Users.ID', ondelete='CASCADE'), nullable=False),
    Column('PackageBaseID', ForeignKey('PackageBases.ID', ondelete='CASCADE'), nullable=False),
    Column('VoteTS', BIGINT(unsigned=True)),
    Index('VoteUsersIDPackageID', 'UsersID', 'PackageBaseID', unique=True),
    Index('VotesPackageBaseID', 'PackageBaseID'),
    Index('VotesUsersID', 'UsersID'),
    mysql_engine='InnoDB',
)


# Record comments for packages
PackageComments = Table(
    'PackageComments', metadata,
    Column('ID', BIGINT(unsigned=True), primary_key=True),
    Column('PackageBaseID', ForeignKey('PackageBases.ID', ondelete='CASCADE'), nullable=False),
    Column('UsersID', ForeignKey('Users.ID', ondelete='SET NULL')),
    Column('Comments', Text, nullable=False),
    Column('RenderedComment', Text, nullable=False),
    Column('CommentTS', BIGINT(unsigned=True), nullable=False, server_default=text("0")),
    Column('EditedTS', BIGINT(unsigned=True)),
    Column('EditedUsersID', ForeignKey('Users.ID', ondelete='SET NULL')),
    Column('DelTS', BIGINT(unsigned=True)),
    Column('DelUsersID', ForeignKey('Users.ID', ondelete='CASCADE')),
    Column('PinnedTS', BIGINT(unsigned=True), nullable=False, server_default=text("0")),
    Index('CommentsPackageBaseID', 'PackageBaseID'),
    Index('CommentsUsersID', 'UsersID'),
    mysql_engine='InnoDB',
)


# Package base co-maintainers
PackageComaintainers = Table(
    'PackageComaintainers', metadata,
    Column('UsersID', ForeignKey('Users.ID', ondelete='CASCADE'), nullable=False),
    Column('PackageBaseID', ForeignKey('PackageBases.ID', ondelete='CASCADE'), nullable=False),
    Column('Priority', INTEGER(unsigned=True), nullable=False),
    Index('ComaintainersPackageBaseID', 'PackageBaseID'),
    Index('ComaintainersUsersID', 'UsersID'),
    mysql_engine='InnoDB',
)


# Package base notifications
PackageNotifications = Table(
    'PackageNotifications', metadata,
    Column('PackageBaseID', ForeignKey('PackageBases.ID', ondelete='CASCADE'), nullable=False),
    Column('UserID', ForeignKey('Users.ID', ondelete='CASCADE'), nullable=False),
    Index('NotifyUserIDPkgID', 'UserID', 'PackageBaseID', unique=True),
    mysql_engine='InnoDB',
)


# Package name blacklist
PackageBlacklist = Table(
    'PackageBlacklist', metadata,
    Column('ID', INTEGER(unsigned=True), primary_key=True),
    Column('Name', String(64), nullable=False, unique=True),
    mysql_engine='InnoDB',
)


# Providers in the official repositories
OfficialProviders = Table(
    'OfficialProviders', metadata,
    Column('ID', INTEGER(unsigned=True), primary_key=True),
    Column('Name', String(64), nullable=False),
    Column('Repo', String(64), nullable=False),
    Column('Provides', String(64), nullable=False),
    Index('ProviderNameProvides', 'Name', 'Provides', unique=True),
    mysql_engine='InnoDB',
)


# Define package request types
RequestTypes = Table(
    'RequestTypes', metadata,
    Column('ID', TINYINT(unsigned=True), primary_key=True),
    Column('Name', String(32), nullable=False, server_default=text("''")),
    mysql_engine='InnoDB',
)


# Package requests
PackageRequests = Table(
    'PackageRequests', metadata,
    Column('ID', BIGINT(unsigned=True), primary_key=True),
    Column('ReqTypeID', ForeignKey('RequestTypes.ID', ondelete="NO ACTION"), nullable=False),
    Column('PackageBaseID', ForeignKey('PackageBases.ID', ondelete='SET NULL')),
    Column('PackageBaseName', String(255), nullable=False),
    Column('MergeBaseName', String(255)),
    Column('UsersID', ForeignKey('Users.ID', ondelete='SET NULL')),
    Column('Comments', Text, nullable=False),
    Column('ClosureComment', Text, nullable=False),
    Column('RequestTS', BIGINT(unsigned=True), nullable=False, server_default=text("0")),
    Column('ClosedTS', BIGINT(unsigned=True)),
    Column('ClosedUID', ForeignKey('Users.ID', ondelete='SET NULL')),
    Column('Status', TINYINT(unsigned=True), nullable=False, server_default=text("0")),
    Index('RequestsPackageBaseID', 'PackageBaseID'),
    Index('RequestsUsersID', 'UsersID'),
    mysql_engine='InnoDB',
)


# Vote information
TU_VoteInfo = Table(
    'TU_VoteInfo', metadata,
    Column('ID', INTEGER(unsigned=True), primary_key=True),
    Column('Agenda', Text, nullable=False),
    Column('User', String(32), nullable=False),
    Column('Submitted', BIGINT(unsigned=True), nullable=False),
    Column('End', BIGINT(unsigned=True), nullable=False),
    Column('Quorum', DECIMAL(2, 2, unsigned=True), nullable=False),
    Column('SubmitterID', ForeignKey('Users.ID', ondelete='CASCADE'), nullable=False),
    Column('Yes', TINYINT(3, unsigned=True), nullable=False, server_default=text("'0'")),
    Column('No', TINYINT(3, unsigned=True), nullable=False, server_default=text("'0'")),
    Column('Abstain', TINYINT(3, unsigned=True), nullable=False, server_default=text("'0'")),
    Column('ActiveTUs', TINYINT(3, unsigned=True), nullable=False, server_default=text("'0'")),
    mysql_engine='InnoDB',
)


# Individual vote records
TU_Votes = Table(
    'TU_Votes', metadata,
    Column('VoteID', ForeignKey('TU_VoteInfo.ID', ondelete='CASCADE'), nullable=False),
    Column('UserID', ForeignKey('Users.ID', ondelete='CASCADE'), nullable=False),
    mysql_engine='InnoDB',
)


# Malicious user banning
Bans = Table(
    'Bans', metadata,
    Column('IPAddress', String(45), primary_key=True),
    Column('BanTS', TIMESTAMP, nullable=False),
    mysql_engine='InnoDB',
)


# Terms and Conditions
Terms = Table(
    'Terms', metadata,
    Column('ID', INTEGER(unsigned=True), primary_key=True),
    Column('Description', String(255), nullable=False),
    Column('URL', String(8000), nullable=False),
    Column('Revision', INTEGER(unsigned=True), nullable=False, server_default=text("1")),
    mysql_engine='InnoDB',
)


# Terms and Conditions accepted by users
AcceptedTerms = Table(
    'AcceptedTerms', metadata,
    Column('UsersID', ForeignKey('Users.ID', ondelete='CASCADE'), nullable=False),
    Column('TermsID', ForeignKey('Terms.ID', ondelete='CASCADE'), nullable=False),
    Column('Revision', INTEGER(unsigned=True), nullable=False, server_default=text("0")),
    mysql_engine='InnoDB',
)


# Rate limits for API
ApiRateLimit = Table(
    'ApiRateLimit', metadata,
    Column('IP', String(45), primary_key=True),
    Column('Requests', INTEGER(11), nullable=False),
    Column('WindowStart', BIGINT(20), nullable=False),
    Index('ApiRateLimitWindowStart', 'WindowStart'),
    mysql_engine='InnoDB',
)
