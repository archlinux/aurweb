-- The MySQL database layout for the AUR.  Certain data
-- is also included such as AccountTypes, PackageLocations, etc.
--
DROP DATABASE AUR;
CREATE DATABASE AUR;

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
	1, 3, 'dev', 'dev@localhost', 'dev');
INSERT INTO Users (ID, AccountTypeID, Username, Email, Passwd) VALUES (
	2, 2, 'tu', 'tu@localhost', 'tu');
INSERT INTO Users (ID, AccountTypeID, Username, Email, Passwd) VALUES (
	3, 1, 'user', 'user@localhost', 'user');


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
INSERT INTO PackageLocations (ID, Location) VALUES (1, 'Unsupported');
INSERT INTO PackageLocations (ID, Location) VALUES (2, 'AUR');
INSERT INTO PackageLocations (ID, Location) VALUES (3, 'Current');
INSERT INTO PackageLocations (ID, Location) VALUES (4, 'Extra');
INSERT INTO PackageLocations (ID, Location) VALUES (5, 'Unstable');


-- Information about the actual packages
--
CREATE TABLE Packages (
	ID INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
	Name CHAR(32) NOT NULL,
	Version CHAR(32) NOT NULL DEFAULT '',
	CategoryID TINYINT UNSIGNED NOT NULL,
	Description CHAR(128) NOT NULL DEFAULT "An Arch Package",
	URL CHAR(255) NOT NULL DEFAULT "http://www.archlinux.org",
	Source CHAR(255) NOT NULL DEFAULT "/dev/null",
	LocationID TINYINT UNSIGNED NOT NULL,
	OutOfDate TINYINT UNSIGNED DEFAULT 0,
	SubmittedTS BIGINT UNSIGNED NOT NULL,
	SubmitterUID INTEGER UNSIGNED NOT NULL DEFAULT 0,
	MaintainerUID INTEGER UNSIGNED NOT NULL DEFAULT 0,
	PRIMARY KEY (ID),
	UNIQUE (Name),
	INDEX (CategoryID),
	INDEX (LocationID),
	INDEX (OutOfDate),
	INDEX (SubmitterUID),
	INDEX (MaintainerUID),
	FOREIGN KEY (CategoryID) REFERENCES PackageCategories(ID) ON DELETE NO ACTION,
	FOREIGN KEY (LocationID) REFERENCES PackageLocations(ID) ON DELETE NO ACTION,
	FOREIGN KEY (SubmitterUID) REFERENCES Users(ID) ON DELETE NO ACTION,
	FOREIGN KEY (MaintainerUID) REFERENCES Users(ID) ON DELETE NO ACTION
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
	FileName CHAR(32) NOT NULL,
	Path CHAR(255) NOT NULL,
	FileSize BIGINT UNSIGNED NOT NULL default 0,
	INDEX (PackageID),
	INDEX (FileName),
	FOREIGN KEY (PackageID) REFERENCES Packages(ID) ON DELETE CASCADE
);

