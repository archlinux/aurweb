#!/usr/bin/python
#
# This script seeds the AUR database with dummy data for
# use during development/testing.  It uses random entries
# from /usr/share/dict/words to create user accounts and
# package names.  It generates the SQL statements to
# insert these users/packages into the AUR database.
#

DBUG      = 1
SEED_FILE = "/usr/share/dict/words"
DB_HOST   = "localhost"
DB_NAME   = "AUR"
DB_USER   = "aur"
DB_PASS   = "aur"
USER_ID   = 5        # Users.ID of first user
PKG_ID    = 1        # Packages.ID of first package
MAX_USERS = 100      # how many users to 'register'
MAX_PKGS  = 250      # how many packages to load
PKG_FILES = (8, 30)  # min/max number of files in a package
VOTING    = (.3, .8) # percentage range for package voting
RANDOM_PATHS = [     # random path locations for package files
	"/usr/bin", "/usr/lib", "/etc", "/etc/rc.d", "/usr/share", "/lib",
	"/var/spool", "/var/log", "/usr/sbin", "/opt", "/usr/X11R6/bin",
	"/usr/X11R6/lib", "/usr/libexec", "/usr/man/man1", "/usr/man/man3",
	"/usr/man/man5", "/usr/X11R6/man/man1", "/etc/profile.d"
]

import random
import time
import os
import sys
import cStringIO

if len(sys.argv) != 2:
	sys.stderr.write("Missing output filename argument");
	raise SystemExit

# Just let python throw the errors if any happen
#
out = open(sys.argv[1], "w")

# make sure the seed file exists
#
if not os.path.exists(SEED_FILE):
	sys.stderr.write("Please install the 'words' Arch package\n");

# Make sure database access will be available
#
try:
	import MySQLdb
except:
	sys.stderr.write("Please install the 'mysql-python' Arch package\n");
	raise SystemExit

# try to connect to database
#
try:
	db = MySQLdb.connect(host = DB_HOST, user = DB_USER,
			db = DB_NAME, passwd = DB_PASS)
	dbc = db.cursor()
except:
	sys.stderr.write("Could not connect to database\n");
	raise SystemExit


# track what users/package names have been used
#
seen_users = {}
seen_pkgs = {}
locations = {}
categories = {}
location_keys = []
category_keys = []
user_keys = []

# some functions to generate random data
#
def genVersion():
	major = random.randrange(0,10)
	minor = random.randrange(0,20)
	if random.randrange(0,2) == 0:
		revision = random.randrange(0,100)
		return "%d.%d.%d" % (major, minor, revision)
	return "%d.%d" % (major, minor)
def genCategory():
	return categories[category_keys[random.randrange(0,len(category_keys))]]
def genLocation():
	return locations[location_keys[random.randrange(0,len(location_keys))]]
def genUID():
	return seen_users[user_keys[random.randrange(0,len(user_keys))]]


# load the words, and make sure there are enough words for users/pkgs
#
if DBUG: print "Grabbing words from seed file..."
fp = open(SEED_FILE, "r")
contents = fp.readlines()
fp.close()
if MAX_USERS > len(contents):
	MAX_USERS = len(contents)
if MAX_PKGS > len(contents):
	MAX_PKGS = len(contents)
if len(contents) - MAX_USERS > MAX_PKGS:
	need_dupes = 0
else:
	need_dupes = 1

# select random usernames
#
if DBUG: print "Generating random user names..."
user_id = USER_ID
while len(seen_users) < MAX_USERS:
	user = random.randrange(0, len(contents))
	word = contents[user].strip().replace("'", "").replace(" ", "_")
	if not seen_users.has_key(user):
		seen_users[word] = user_id
		user_id += 1
user_keys = seen_users.keys()

# select random package names
#
if DBUG: print "Generating random package names..."
num_pkgs = PKG_ID
while len(seen_pkgs) < MAX_PKGS:
	pkg = random.randrange(0, len(contents))
	word = contents[pkg].strip().replace("'", "").replace(" ", "_")
	if not need_dupes:
		if not seen_pkgs.has_key(word) and not seen_users.has_key(word):
			seen_pkgs[word] = num_pkgs
			num_pkgs += 1
	else:
		if not seen_pkgs.has_key(word):
			seen_pkgs[word] = num_pkgs
			num_pkgs += 1

# Load package categories from database
#
if DBUG: print "Loading package categories/locations..."
q = "SELECT * FROM PackageCategories"
dbc.execute(q)
row = dbc.fetchone()
while row:
	categories[row[1]] = row[0]
	row = dbc.fetchone()
category_keys = categories.keys()

# Load package locations from database
#
q = "SELECT * FROM PackageLocations"
dbc.execute(q)
row = dbc.fetchone()
while row:
	locations[row[1]] = row[0]
	row = dbc.fetchone()
location_keys = locations.keys()

# done with the database
#
dbc.close()
db.close()

# Begin by creating the User statements
#
if DBUG: print "Creating SQL statements for users.",
count = 0
for u in user_keys:
	s = """\
INSERT INTO Users (ID, AccountTypeID, Username, Email, Passwd)
    VALUES (%d, 1, '%s', '%s@example.com', '%s');
	""" % (seen_users[u], u, u, u)
	out.write(s)
	if count % 10 == 0:
		if DBUG: print ".",
	count += 1
if DBUG: print "."

# Create the package statements
#
if DBUG: print "Creating SQL statements for packages.",
count = 0
for p in seen_pkgs.keys():
	s = """\
INSERT INTO Packages (ID, Name, Version, CategoryID, LocationID,
    SubmittedTS, SubmitterUID, MaintainerUID)
    VALUES (%d, '%s', '%s', %d, %d, %d, %d, 1);
	""" % (seen_pkgs[p], p, genVersion(), genCategory(), genLocation(),
			long(time.time()), genUID())
	out.write(s)
	if count % 100 == 0:
		if DBUG: print ".",
	count += 1

	# Create package contents
	#
	num_files = random.randrange(PKG_FILES[0], PKG_FILES[1])
	files = {}
	for f in range(num_files):
		loc = RANDOM_PATHS[random.randrange(len(RANDOM_PATHS))]
		if "lib" in loc:
			path = loc + "/lib" + p + ".so"
		elif "man" in loc:
			path = loc + "/" + p + "." + loc[-1] + ".gz"
		elif "share" in loc:
			path = loc + "/" + p + "/sounds/" + p + ".wav"
		elif "profile" in loc:
			path = loc + "/" + p + ".sh"
		elif "rc.d" in loc:
			path = loc + "/" + p
		elif "etc" in loc:
			path = loc + "/" + p + ".conf"
		elif "opt" in loc:
			path = loc + "/" + p + "/bin/" + p
		else:
			path = loc + "/" + p
		if not files.has_key(path):
			files[path] = 1
			s = """\
INSERT INTO PackageContents (PackageID, FileName, Path, FileSize)
    VALUES (%d, '%s', '%s', %d);
			""" % (seen_pkgs[p], os.path.basename(path), path,
					random.randrange(0,99999999))
			out.write(s)
if DBUG: print "."

# Cast votes
#
if DBUG: print "Casting votes for packages.",
count = 0
for u in user_keys:
	num_votes = random.randrange(len(seen_pkgs)*VOTING[0],
			len(seen_pkgs)*VOTING[1])
	pkgvote = {}
	for v in range(num_votes):
		pkg = random.randrange(0, len(seen_pkgs))
		if not pkgvote.has_key(pkg):
			s = """\
INSERT INTO PackageVotes (UsersID, PackageID) VALUES (%d, %d);
			""" % (seen_users[u], pkg)
			pkgvote[pkg] = 1
			out.write(s)
			if count % 100 == 0:
				if DBUG: print ".",
			count += 1

# close output file
#
out.write("\n")
out.close()

if DBUG: print "."
if DBUG: print "Done."

