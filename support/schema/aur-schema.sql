-- The MySQL database layout for the AUR.  Certain data
-- is also included such as AccountTypes, PackageLocations, etc.
--
DROP DATABASE aur;
CREATE DATABASE aur;
use aur;

-- Define the Account Types for the AUR.
--
CREATE TABLE AccountTypes (
	ID TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
	AccountType char(32) NOT NULL DEFAULT '',
	PRIMARY KEY (ID)
);
INSERT INTO AccountTypes (ID, AccountType) VALUES (1, 'User');
INSERT INTO AccountTypes (ID, AccountType) VALUES (2, 'Trusted User');
INSERT INTO AccountTypes (ID, AccountType) VALUES (3, 'Developer');


-- User information for each user regardless of type.
--
CREATE TABLE Users (
	ID INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
	AccountTypeID TINYINT UNSIGNED NOT NULL DEFAULT 1,
	Suspended TINYINT UNSIGNED NOT NULL DEFAULT 0,
	Username CHAR(32) NOT NULL,
	Email CHAR(64) NOT NULL,
	Passwd CHAR(32) NOT NULL,
	RealName CHAR(64) NOT NULL DEFAULT '',
	LangPreference CHAR(2) NOT NULL DEFAULT 'en',
	IRCNick CHAR(32) NOT NULL DEFAULT '',
	LastVoted BIGINT UNSIGNED NOT NULL DEFAULT 0,
	NewPkgNotify TINYINT UNSIGNED NOT NULL DEFAULT 0,
	PRIMARY KEY (ID),
	UNIQUE (Username),
	UNIQUE (Email),
	INDEX (AccountTypeID),
	INDEX (NewPkgNotify),
	FOREIGN KEY (AccountTypeID) REFERENCES AccountTypes(ID) ON DELETE NO ACTION
);
-- A default developer account for testing purposes
INSERT INTO Users (ID, AccountTypeID, Username, Email, Passwd) VALUES (
	1, 3, 'dev', 'dev@localhost', MD5('dev'));
INSERT INTO Users (ID, AccountTypeID, Username, Email, Passwd) VALUES (
	2, 2, 'tu', 'tu@localhost', MD5('tu'));
INSERT INTO Users (ID, AccountTypeID, Username, Email, Passwd) VALUES (
	3, 1, 'user', 'user@localhost', MD5('user'));


-- Track Users logging in/out of AUR web site.
--
CREATE TABLE Sessions (
	UsersID INTEGER UNSIGNED NOT NULL,
	SessionID CHAR(32) NOT NULL,
	LastUpdateTS BIGINT UNSIGNED NOT NULL,
	FOREIGN KEY (UsersID) REFERENCES Users(ID),
	UNIQUE (SessionID)
);


-- Categories for grouping packages when they reside in
-- Unsupported or the AUR - based on the categories defined
-- in 'extra'.
--
CREATE TABLE PackageCategories (
	ID TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
	Category CHAR(32) NOT NULL,
	PRIMARY KEY (ID)
);
INSERT INTO PackageCategories (Category) VALUES ('none');
INSERT INTO PackageCategories (Category) VALUES ('daemons');
INSERT INTO PackageCategories (Category) VALUES ('devel');
INSERT INTO PackageCategories (Category) VALUES ('editors');
INSERT INTO PackageCategories (Category) VALUES ('emulators');
INSERT INTO PackageCategories (Category) VALUES ('games');
INSERT INTO PackageCategories (Category) VALUES ('gnome');
INSERT INTO PackageCategories (Category) VALUES ('i18n');
INSERT INTO PackageCategories (Category) VALUES ('kde');
INSERT INTO PackageCategories (Category) VALUES ('lib');
INSERT INTO PackageCategories (Category) VALUES ('modules');
INSERT INTO PackageCategories (Category) VALUES ('multimedia');
INSERT INTO PackageCategories (Category) VALUES ('network');
INSERT INTO PackageCategories (Category) VALUES ('office');
INSERT INTO PackageCategories (Category) VALUES ('science');
INSERT INTO PackageCategories (Category) VALUES ('system');
INSERT INTO PackageCategories (Category) VALUES ('x11');
INSERT INTO PackageCategories (Category) VALUES ('xfce');


-- The various repositories that a package could live in.
--
CREATE TABLE PackageLocations (
	ID TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
	Location CHAR(32) NOT NULL,
	PRIMARY KEY (ID)
);
INSERT INTO PackageLocations (Location) VALUES ('none');
INSERT INTO PackageLocations (Location) VALUES ('unsupported');
INSERT INTO PackageLocations (Location) VALUES ('community');
INSERT INTO PackageLocations (Location) VALUES ('current');
INSERT INTO PackageLocations (Location) VALUES ('extra');
INSERT INTO PackageLocations (Location) VALUES ('unstable');


-- Information about the actual packages
--
CREATE TABLE Packages (
	ID INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
	Name CHAR(64) NOT NULL,
	Version CHAR(32) NOT NULL DEFAULT '',
	CategoryID TINYINT UNSIGNED NOT NULL DEFAULT 1,
	Description CHAR(255) NOT NULL DEFAULT "An Arch Package",
	URL CHAR(255) NOT NULL DEFAULT "http://www.archlinux.org",
	DummyPkg TINYINT UNSIGNED NOT NULL DEFAULT 0,         -- 1=>dummy
	FSPath CHAR(255) NOT NULL DEFAULT '',
	URLPath CHAR(255) NOT NULL DEFAULT '',
	License CHAR(40) NOT NULL DEFAULT '',
	LocationID TINYINT UNSIGNED NOT NULL DEFAULT 1,
	NumVotes INTEGER UNSIGNED NOT NULL DEFAULT 0,
	OutOfDate TINYINT UNSIGNED DEFAULT 0,
	SubmittedTS BIGINT UNSIGNED NOT NULL,
	ModifiedTS BIGINT UNSIGNED NOT NULL,
	SubmitterUID INTEGER UNSIGNED NOT NULL DEFAULT 0,     -- who submitted it?
	MaintainerUID INTEGER UNSIGNED NOT NULL DEFAULT 0,    -- User
	AURMaintainerUID INTEGER UNSIGNED NOT NULL DEFAULT 0, -- TU/Dev
	FULLTEXT (Name,Description),
	PRIMARY KEY (ID),
	UNIQUE (Name),
	INDEX (CategoryID),
	INDEX (LocationID),
	INDEX (DummyPkg),
	INDEX (OutOfDate),
	INDEX (NumVotes),
	INDEX (SubmitterUID),
	INDEX (MaintainerUID),
	INDEX (AURMaintainerUID),
	FOREIGN KEY (CategoryID) REFERENCES PackageCategories(ID) ON DELETE NO ACTION,
	FOREIGN KEY (LocationID) REFERENCES PackageLocations(ID) ON DELETE NO ACTION,
	FOREIGN KEY (SubmitterUID) REFERENCES Users(ID) ON DELETE NO ACTION,
	FOREIGN KEY (MaintainerUID) REFERENCES Users(ID) ON DELETE NO ACTION,
	FOREIGN KEY (AURMaintainerUID) REFERENCES Users(ID) ON DELETE NO ACTION
);


-- Track which dependencies a package has
--
CREATE TABLE PackageDepends (
	PackageID INTEGER UNSIGNED NOT NULL,
	DepPkgID INTEGER UNSIGNED NOT NULL,
	DepCondition VARCHAR(20),
	INDEX (PackageID)
);


-- Track which sources a package has
--
CREATE TABLE PackageSources (
	PackageID INTEGER UNSIGNED NOT NULL,
	Source CHAR(255) NOT NULL DEFAULT "/dev/null",
	INDEX (PackageID)
);


-- Track votes for packages
--
CREATE TABLE PackageVotes (
	UsersID INTEGER UNSIGNED NOT NULL,
	PackageID INTEGER UNSIGNED NOT NULL,
	INDEX (UsersID),
	INDEX (PackageID),
	FOREIGN KEY (UsersID) REFERENCES Users(ID) ON DELETE CASCADE,
	FOREIGN KEY (PackageID) REFERENCES Packages(ID) ON DELETE CASCADE
);


-- The individual files and their file system location.
--
CREATE TABLE PackageContents (
	PackageID INTEGER UNSIGNED NOT NULL,
	FSPath CHAR(255) NOT NULL DEFAULT '',
	URLPath CHAR(255) NOT NULL DEFAULT '',
	FileSize BIGINT UNSIGNED NOT NULL default 0,
	INDEX (PackageID),
	FOREIGN KEY (PackageID) REFERENCES Packages(ID) ON DELETE CASCADE
);

-- Record comments for packages
--
CREATE TABLE PackageComments (
	ID BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
	PackageID INTEGER UNSIGNED NOT NULL,
	UsersID INTEGER UNSIGNED NOT NULL,
	Comments TEXT NOT NULl DEFAULT '',
	CommentTS BIGINT UNSIGNED NOT NULL DEFAULT 0,
	DelUsersID INTEGER UNSIGNED NOT NULL DEFAULT 0,
	PRIMARY KEY (ID),
	INDEX (UsersID),
	INDEX (PackageID),
	FOREIGN KEY (UsersID) REFERENCES Users(ID) ON DELETE CASCADE,
	FOREIGN KEY (DelUsersID) REFERENCES Users(ID) ON DELETE CASCADE,
	FOREIGN KEY (PackageID) REFERENCES Packages(ID) ON DELETE CASCADE
);

-- Comment addition notifications
--
CREATE TABLE CommentNotify (
	PkgID INTEGER UNSIGNED NOT NULL,
	UserID INTEGER UNSIGNED NOT NULL,
	FOREIGN KEY (PkgID) REFERENCES Packages(ID) ON DELETE CASCADE,
	FOREIGN KEY (UserID) REFERENCES Users(ID) ON DELETE CASCADE
);

-- Vote information
--
CREATE TABLE IF NOT EXISTS TU_VoteInfo (
  ID int(10) unsigned NOT NULL auto_increment,
  Agenda text collate latin1_general_ci NOT NULL,
  User char(32) collate latin1_general_ci NOT NULL,
  Submitted bigint(20) unsigned NOT NULL,
  End bigint(20) unsigned NOT NULL,
  SubmitterID int(10) unsigned NOT NULL,
  Yes tinyint(3) unsigned NOT NULL default '0',
  No tinyint(3) unsigned NOT NULL default '0',
  Abstain tinyint(3) unsigned NOT NULL default '0',
  PRIMARY KEY  (ID)
);

-- Individual vote records
--
CREATE TABLE IF NOT EXISTS TU_Votes (
  VoteID int(10) unsigned NOT NULL,
  UserID int(10) unsigned NOT NULL
);

