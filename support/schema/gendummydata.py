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
MAX_USERS = 1000     # how many users to 'register'
MAX_DEVS  = .1       # what percentage of MAX_USERS are Developers
MAX_TUS   = .2       # what percentage of MAX_USERS are Trusted Users
MAX_PKGS  = 2500     # how many packages to load
PKG_FILES = (8, 30)  # min/max number of files in a package
VOTING    = (.1, .4) # percentage range for package voting
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
def genVersion(location_id=0):
	ver = []
	ver.append("%d" % random.randrange(0,10))
	ver.append("%d" % random.randrange(0,20))
	if random.randrange(0,2) == 0:
		ver.append("%d" % random.randrange(0,100))
	if location_id == 2: # the package is in the AUR
		return ".".join(ver) + "-u%d" % random.randrange(1,11)
	else:
		return ".".join(ver) + "%d" % random.randrange(1,11)
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

# developer/tu IDs
#
developers = []
trustedusers = []
has_devs = 0
has_tus = 0

# Begin by creating the User statements
#
if DBUG: print "Creating SQL statements for users.",
count = 0
for u in user_keys:
	account_type = 1  # default to normal user
	if not has_devs or not has_tus:
		account_type = random.randrange(1, 4)
		if account_type == 3 and not has_devs:
			# this will be a dev account
			#
			developers.append(seen_users[u])
			if len(developers) >= MAX_DEVS * MAX_USERS:
				has_devs = 1
		elif account_type == 2 and not has_tus:
			# this will be a trusted user account
			#
			trustedusers.append(seen_users[u])
			if len(trustedusers) >= MAX_TUS * MAX_USERS:
				has_tus = 1
		else:
			# a normal user account
			#
			pass
	
	s = "INSERT INTO Users (ID, AccountTypeID, Username, Email, Passwd) VALUES (%d, %d, '%s', '%s@example.com', '%s');\n" % (seen_users[u], account_type, u, u, u)
	out.write(s)
	if count % 10 == 0:
		if DBUG: print ".",
	count += 1
if DBUG: print "."
if DBUG:
	print "Number of developers:", len(developers)
	print "Number of trusted users:", len(trustedusers)
	print "Number of users:", (MAX_USERS-len(developers)-len(trustedusers))
	print "Number of packages:", MAX_PKGS

# Create the package statements
#
if DBUG: print "Creating SQL statements for packages.",
count = 0
for p in seen_pkgs.keys():
	if count % 2 == 0:
		muid = developers[random.randrange(0,len(developers))]
	else:
		muid = trustedusers[random.randrange(0,len(trustedusers))]
	if count % 20 == 0: # every so often, there are orphans...
		muid = 0

	location_id = genLocation()
	if location_id == 1: # unsupported pkgs don't have a maintainer
		muid = 0

	s = "INSERT INTO Packages (ID, Name, Version, CategoryID, LocationID, SubmittedTS, SubmitterUID, MaintainerUID) VALUES (%d, '%s', '%s', %d, %d, %d, %d, %d);\n" % (seen_pkgs[p], p, genVersion(location_id), genCategory(),
			location_id, long(time.time()), genUID(), muid)
	out.write(s)
	if count % 100 == 0:
		if DBUG: print ".",
	count += 1

	if location_id == 1: # Unsupported - just a PKGBUILD and maybe other stuff
		others = random.randrange(0,3)
		s = "INSERT INTO PackageContents (PackageID, FileName, Path, FileSize) VALUES (%d, '%s', '%s', %d);\n" % (seen_pkgs[p], "PKGBUILD", "/home/aur/incoming/%s/PKGBUILD" % p,
				random.randrange(0,999))
		out.write(s)
		if others == 0:
			s = "INSERT INTO PackageContents (PackageID, FileName, Path, FileSize) VALUES (%d, '%s', '%s', %d);\n" % (seen_pkgs[p], "%s.patch" % p,
					"/home/aur/incoming/%s/%s.patch" % (p,p),
					random.randrange(0,999))
			out.write(s)

		elif others == 1:
			s = "INSERT INTO PackageContents (PackageID, FileName, Path, FileSize) VALUES (%d, '%s', '%s', %d);\n" % (seen_pkgs[p], "%s.patch" % p,
					"/home/aur/incoming/%s/%s.patch" % (p,p),
					random.randrange(0,999))
			out.write(s)
			s = "INSERT INTO PackageContents (PackageID, FileName, Path, FileSize) VALUES (%d, '%s', '%s', %d);\n" % (seen_pkgs[p], "arch.patch",
					"/home/aur/incoming/%s/arch.patch" % p,
					random.randrange(0,999))
			out.write(s)

		elif others == 2:
			s = "INSERT INTO PackageContents (PackageID, FileName, Path, FileSize) VALUES (%d, '%s', '%s', %d);\n" % (seen_pkgs[p], "%s.patch" % p,
					"/home/aur/incoming/%s/%s.patch" % (p,p),
					random.randrange(0,999))
			out.write(s)
			s = "INSERT INTO PackageContents (PackageID, FileName, Path, FileSize) VALUES (%d, '%s', '%s', %d);\n" % (seen_pkgs[p], "arch.patch",
					"/home/aur/incoming/%s/arch.patch" % p,
					random.randrange(0,999))
			out.write(s)
			s = "INSERT INTO PackageContents (PackageID, FileName, Path, FileSize) VALUES (%d, '%s', '%s', %d);\n" % (seen_pkgs[p], "%s.install" % p,
					"/home/aur/incoming/%s/%s.install" % (p,p),
					random.randrange(0,999))
			out.write(s)

	else:
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
				s = "INSERT INTO PackageContents (PackageID, FileName, Path, FileSize) VALUES (%d, '%s', '%s', %d);\n" % (seen_pkgs[p], os.path.basename(path), path,
						random.randrange(0,99999999))
				out.write(s)
if DBUG: print "."

# Cast votes
#
track_votes = {}
if DBUG: print "Casting votes for packages.",
count = 0
for u in user_keys:
	num_votes = random.randrange(int(len(seen_pkgs)*VOTING[0]),
			int(len(seen_pkgs)*VOTING[1]))
	pkgvote = {}
	for v in range(num_votes):
		pkg = random.randrange(0, len(seen_pkgs))
		if not pkgvote.has_key(pkg):
			s = "INSERT INTO PackageVotes (UsersID, PackageID) VALUES (%d, %d);\n" % (seen_users[u], pkg)
			pkgvote[pkg] = 1
			if not track_votes.has_key(pkg):
				track_votes[pkg] = 0
			track_votes[pkg] += 1
			out.write(s)
			if count % 100 == 0:
				if DBUG: print ".",
			count += 1

# Update statements for package votes
#
for p in track_votes.keys():
	s = "UPDATE Packages SET NumVotes = %d WHERE ID = %d;\n" % (track_votes[p], p)
	out.write(s)

# close output file
#
out.write("\n")
out.close()

if DBUG: print "."
if DBUG: print "Done."

