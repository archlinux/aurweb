-- The MySQL database layout for the AUR.  Certain data
-- is also included such as AccountTypes, PackageLocations, etc.
--

-- Define the Account Types for the AUR.
--
CREATE TABLE AccountTypes (
	ID UNSIGNED TINYINT NOT NULL AUTO_INCREMENT,
	AccountType char(32) NOT NULL DEFAULT '',
	PRIMARY KEY (ID)
);
INSERT INTO TABLE (ID, AccountType) VALUES (1, 'User');
INSERT INTO TABLE (ID, AccountType) VALUES (2, 'Trusted User');
INSERT INTO TABLE (ID, AccountType) VALUES (3, 'Developer');


-- User information for each user regardless of type.
--
CREATE TABLE Users (
	ID UNSIGNED INTEGER NOT NULL AUTO_INCREMENT,
  AccountTypeID UNSIGNED TINYINT NOT NULL DEFAULT 1,
	Suspended UNSIGNED TINYINT NOT NULL DEFAULT 0,
	Email CHAR(64) NOT NULL,
	Passwd CHAR(32) NOT NULL,
	RealName CHAR(64) NOT NULL DEFAULT '',
	IRCNick CHAR(32) NOT NULL DEFAULT '',
	LastVoted UNSIGNED BIGINT NOT NULL DEFAULT 0,
	NewPkgNotify UNSIGNED TINYINT NOT NULL DEFAULT 0,
	PRIMARY KEY (ID),
	UNIQUE INDEX Emailx (Email),
	INDEX AccountTypeIDx (AccountTypeID),
	INDEX NewPkgNotifyx (NewPkgNotify),
	FOREIGN KEY AccountTypeIDr REFERENCES AccountTypes (ID)
);
-- A default developer account for testing purposes
INSERT INTO Users (ID, AccountTypeID, Email, Passwd) VALUES (
	1, 3, 'root@localhost', 'changeme');


-- Track Users logging in/out of AUR web site.
--
CREATE TABLE Sessions (
	UsersID UNSIGNED INTEGER NOT NULL,
	SessionID CHAR(32) NOT NULL,
	LastUpdateTS UNSIGNED BIGINT NOT NULL,
	FOREIGN KEY UsersIDr REFERENCES Users (ID)
);


-- Categories for grouping packages when they reside in
-- Unsupported or the AUR - based on the categories defined
-- in 'extra'.
--
CREATE TABLE PackageCategories (
	ID UNSIGNED TINYINT NOT NULL AUTO_INCREMENT,
	Category CHAR(32) NOT NULL,
	PRIMARY KEY (ID)
);
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
	ID UNSIGNED TINYINT NOT NULL AUTO_INCREMENT,
	Location CHAR(32) NOT NULL,
	PRIMARY KEY (ID)
);
INSERT INTO PackageLocations (ID, Location) VALUES (1, 'Unsupported');
INSERT INTO PackageLocations (ID, Location) VALUES (2, 'AUR');
INSERT INTO PackageLocations (ID, Location) VALUES (3, 'Current');
INSERT INTO PackageLocations (ID, Location) VALUES (4, 'Extra');
INSERT INTO PackageLocations (ID, Location) VALUES (5, 'Unstable');


-- Information about the actual packages
--
CREATE TABLE Packages (
	ID UNSIGNED INTEGER NOT NULL AUTO_INCREMENT,
	Name CHAR(32) NOT NULL,
	Version CHAR(32) NOT NULL DEFAULT '',
	CategoryID UNSIGNED TINYINT NOT NULL,
	Description CHAR(128) NOT NULL DEFAULT "An Arch Package",
	URL CHAR(256) NOT NULL DEFAULT "http://www.archlinux.org",
	Source CHAR(256) NOT NULL DEFAULT "/dev/null",
	LocationID UNSIGNED TINYINT NOT NULL,
	OutOfDate UNSIGNED TINYINT DEFAULT 0,
	SubmittedTS UNSIGNED BIGINT NOT NULL,
	SubmitterUID UNSIGNED INTEGER NOT NULL DEFAULT 0,
	MaintainerUID UNSIGNED INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY (ID),
	UNIQUE INDEX Namex (Name),
	INDEX CategoryIDx (CategoryID),
	INDEX LocationIDx (LocationID),
	INDEX OutOfDatex (OutOfDate),
	INDEX SubmitterUIDx (SubmitterUID),
	INDEX MaintainerUIDx (MaintainerUID),
	FOREIGN KEY CategoryIDr REFERENCES PackageCategories (ID),
	FOREIGN KEY LocationIDr REFERENCES PackageLocations (ID)
	FOREIGN KEY SubmitterUIDr REFERENCES Users (ID)
	FOREIGN KEY MaintainerUIDr REFERENCES Users (ID)
);


-- Track votes for packages
--
CREATE TABLE PackageVotes (
	UsersID UNSIGNED INTEGER NOT NULL,
	PackageID UNSIGNED INTEGER NOT NULL,
	PRIMARY KEY (ID),
	FOREIGN KEY UsersIDx REFERENCES Users (ID),
	FOREIGN KEY PackageIDx REFERENCES Packages (ID)
);


-- The individual files and their file system location.
--
CREATE TABLE PackageContents (
	PackageID UNSIGNED INTEGER NOT NULL,
	Path CHAR(256) NOT NULL,
	INDEX PackageIDx (PackageID)
);

