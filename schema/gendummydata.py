#!/usr/bin/env python3
"""
usage: gendummydata.py outputfilename.sql
"""

#
# This script seeds the AUR database with dummy data for
# use during development/testing.  It uses random entries
# from /usr/share/dict/words to create user accounts and
# package names.  It generates the SQL statements to
# insert these users/packages into the AUR database.
#

import argparse
import hashlib
import logging
import os
import random
import time
from datetime import UTC, datetime
from typing import cast

import bcrypt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate database dummy data")
    _ = parser.add_argument(
        "--delete-data",
        action="store_true",
        help="Add DELETE statements to clear the database before inserting",
    )
    _ = parser.add_argument(
        "--max-users",
        type=int,
        default=int(os.environ.get("MAX_USERS", 38000)),
        metavar="n",
        help="number of users to generate",
    )
    _ = parser.add_argument(
        "--max-packages",
        type=int,
        default=int(os.environ.get("MAX_PKGS", 32000)),
        metavar="n",
        help="number of packages to generate",
    )
    _ = parser.add_argument(
        "--min-pkg-depends",
        type=int,
        default=1,
        metavar="n",
        help="number of minimum package depends",
    )
    _ = parser.add_argument(
        "--max-pkg-depends",
        type=int,
        default=15,
        metavar="n",
        help="number of maximum package depends",
    )
    _ = parser.add_argument(
        "--min-pkg-relations",
        type=int,
        default=1,
        metavar="n",
        help="number of minimum package relations",
    )
    _ = parser.add_argument(
        "--max-pkg-relations",
        type=int,
        default=5,
        metavar="n",
        help="number of maximum package relations",
    )
    _ = parser.add_argument(
        "--min-pkg-sources",
        type=int,
        default=1,
        metavar="n",
        help="number of minimum package sources",
    )
    _ = parser.add_argument(
        "--max-pkg-sources",
        type=int,
        default=3,
        metavar="n",
        help="number of maximum package sources",
    )
    _ = parser.add_argument(
        "--min-pkg-comments",
        type=int,
        default=1,
        metavar="n",
        help="number of minimum package comments",
    )
    _ = parser.add_argument(
        "--max-pkg-comments",
        type=int,
        default=5,
        metavar="n",
        help="number of maximum package comments",
    )
    _ = parser.add_argument(
        "--optdepends-description",
        type=float,
        default=0.75,
        metavar="f",
        help="Probability that optdepends contains a description",
    )
    _ = parser.add_argument(
        "--split-packages",
        type=float,
        default=0.1,
        metavar="f",
        help="Probability that a package is part of a split package base",
    )
    _ = parser.add_argument(
        "--official-packages",
        type=float,
        default=0.1,
        metavar="f",
        help="Probability that a dependency is an official repo package",
    )
    _ = parser.add_argument(
        "--none-existing-depends",
        type=float,
        default=0.1,
        metavar="f",
        help="Probability that a dependency does not exist",
    )
    _ = parser.add_argument(
        "--open-proposals",
        type=int,
        default=int(os.environ.get("OPEN_PROPOSALS", 15)),
        metavar="n",
        help="number of open package maintainer proposals",
    )
    _ = parser.add_argument(
        "--closed-proposals",
        type=int,
        default=int(os.environ.get("CLOSE_PROPOSALS", 50)),
        metavar="n",
        help="number of closed package maintainer proposals",
    )
    _ = parser.add_argument(
        "--package-voting",
        type=float,
        default=0.001,
        metavar="f",
        help="percentage range for package voting",
    )
    _ = parser.add_argument("output_file", metavar="FILE", help="Output filename")
    return parser.parse_args()


args = parse_args()
LOG_LEVEL = logging.DEBUG  # logging level. set to logging.INFO to reduce output
SEED_FILE = "/usr/share/dict/words"
USER_ID = 5  # Users.ID of first bogus user
PKG_ID = 1  # Packages.ID of first package
# how many users to 'register'
MAX_USERS = cast(int, args.max_users)
MAX_DEVS = 0.1  # what percentage of MAX_USERS are Developers
MAX_PMS = 0.2  # what percentage of MAX_USERS are Package Maintainers
# how many packages to load
MAX_PKGS = cast(int, args.max_packages)
PKG_DEPS = (
    cast(int, args.min_pkg_depends),
    cast(int, args.max_pkg_depends),
)  # min/max depends a package has
PKG_RELS = (
    cast(int, args.min_pkg_relations),
    cast(int, args.max_pkg_relations),
)  # min/max relations a package has
PKG_SRC = (
    cast(int, args.min_pkg_sources),
    cast(int, args.max_pkg_sources),
)  # min/max sources a package has
PKG_CMNTS = (
    cast(int, args.min_pkg_comments),
    cast(int, args.max_pkg_comments),
)  # min/max comments a package has
PKG_OPTS_DESC_PROBABILITY = cast(float, args.optdepends_description)
PKG_SPLIT_PROBABILITY = cast(float, args.split_packages)
CATEGORIES_COUNT = 17  # the number of categories from aur-schema
VOTING = (0, cast(float, args.package_voting))  # percentage range for package voting
OPEN_PROPOSALS = cast(int, args.open_proposals)
CLOSE_PROPOSALS = cast(int, args.closed_proposals)
RANDOM_TLDS = ("edu", "com", "org", "net", "tw", "ru", "pl", "de", "es")
RANDOM_URL = ("http://www.", "ftp://ftp.", "http://", "ftp://")
RANDOM_LOCS = ("pub", "release", "files", "downloads", "src")
FORTUNE_FILE = os.environ.get("FORTUNE_FILE", "/usr/share/fortune/cookie")
# some official repo package so we can live test all code paths, including provides
OFFICIAL_PACKAGES = ["linux", "coreutils", "gcc", "clang", "rust", "netcat", "cargo"]
OFFICIAL_PACKAGE_PROBABILITY = cast(float, args.official_packages)
NONE_EXISTING_PACKAGE_PROBABILITY = cast(float, args.none_existing_depends)

# setup logging
logformat = "%(levelname)s: %(message)s"
logging.basicConfig(format=logformat, level=LOG_LEVEL)
log = logging.getLogger()

# make sure the seed file exists
#
if not os.path.exists(SEED_FILE):
    log.error("Please install the 'words' Arch package")
    raise SystemExit(1)

# make sure comments can be created
#
if not os.path.exists(FORTUNE_FILE):
    log.error("Please install the 'fortune-mod' Arch package")
    raise SystemExit(1)

# track what users/package names have been used
#
seen_users = {}
seen_pkgs = {}
user_keys = []


# some functions to generate random data
#
def genVersion():
    ver = []
    ver.append("%d" % random.randrange(0, 10))
    ver.append("%d" % random.randrange(0, 20))
    if random.randrange(0, 2) == 0:
        ver.append("%d" % random.randrange(0, 100))
    return ".".join(ver) + "-%d" % random.randrange(1, 11)


def genCategory():
    return random.randrange(1, CATEGORIES_COUNT)


def genUID():
    return seen_users[user_keys[random.randrange(0, len(user_keys))]]


def genFortune():
    return fortunes[random.randrange(0, len(fortunes))].replace("'", "")


# load the words, and make sure there are enough words for users/pkgs
#
log.debug("Grabbing words from seed file...")
fp = open(SEED_FILE, "r", encoding="utf-8")
contents = fp.readlines()
fp.close()
if MAX_USERS > len(contents):
    MAX_USERS = len(contents)
if MAX_PKGS > len(contents):
    MAX_PKGS = len(contents)

need_dupes = 0
if not len(contents) - MAX_USERS > MAX_PKGS:
    need_dupes = 1


def normalize(unicode_data):
    """We only accept ascii for usernames. Also use this to normalize
    package names; our database utf8mb4 collations compare with Unicode
    Equivalence."""
    return unicode_data.encode("ascii", "ignore").decode("ascii")


# select random usernames
#
log.debug("Generating random user names...")
user_id = USER_ID
while len(seen_users) < MAX_USERS:
    user = random.randrange(0, len(contents))
    word = contents[user].replace("'", "").replace(".", "").replace(" ", "_")
    word = normalize(word.strip().lower())
    if word not in seen_users:
        seen_users[word] = user_id
        user_id += 1
user_keys = list(seen_users.keys())


# select random package names
#
log.debug("Generating random package names...")
num_pkgs = PKG_ID
pkgbases = {}
while len(seen_pkgs) < MAX_PKGS:
    pkg = random.randrange(0, len(contents))
    word = contents[pkg].replace("'", "").replace(".", "").replace(" ", "_")
    word = normalize(word.strip().lower())
    if word in seen_pkgs:
        continue
    if not need_dupes and word in seen_users:
        continue
    pkgbase = num_pkgs
    if pkgbases and random.random() < PKG_SPLIT_PROBABILITY:
        pkgbase = random.choice(list(pkgbases.values()))
    seen_pkgs[word] = num_pkgs
    pkgbases[word] = pkgbase
    num_pkgs += 1

# free up contents memory
#
contents = None

# developer/PM IDs
#
developers = []
packagemaintainers = []
has_devs = 0
has_pms = 0

# Just let python throw the errors if any happen
#
out = open(args.output_file, "w", encoding="utf-8")
out.write("BEGIN;\n")
if cast(bool, args.delete_data):
    out.write("DELETE FROM Users;\n")
    out.write("DELETE FROM Packages;\n")
    out.write("DELETE FROM PackageBases;\n")

# Begin by creating the User statements
#
log.debug("Creating SQL statements for users.")
for u in user_keys:
    account_type = 1  # default to normal user
    if not has_devs or not has_pms:
        account_type = random.randrange(1, 4)
        if account_type == 3 and not has_devs:
            # this will be a dev account
            #
            developers.append(seen_users[u])
            if len(developers) >= MAX_DEVS * MAX_USERS:
                has_devs = 1
        elif account_type == 2 and not has_pms:
            # this will be a package maintainer account
            #
            packagemaintainers.append(seen_users[u])
            if len(packagemaintainers) >= MAX_PMS * MAX_USERS:
                has_pms = 1
        else:
            # a normal user account
            #
            pass

    # For dummy data, we just use 4 salt rounds.
    salt = bcrypt.gensalt(rounds=4).decode()

    # "{salt}{username}"
    to_hash = f"{salt}{u}"

    h = hashlib.new("md5")
    h.update(to_hash.encode())
    s = (
        "INSERT INTO Users (ID, AccountTypeID, Username, Email, Passwd, Salt)"
        " VALUES (%d, %d, '%s', '%s@example.com', '%s', '%s');\n"
    )
    s = s % (seen_users[u], account_type, u, u, h.hexdigest(), salt)
    out.write(s)

log.debug("Number of developers: %d" % len(developers))
log.debug("Number of package maintainers: %d" % len(packagemaintainers))
log.debug(
    "Number of users: %d" % (MAX_USERS - len(developers) - len(packagemaintainers))
)
log.debug("Number of packages: %d" % MAX_PKGS)

log.debug("Gathering text from fortune file...")
fp = open(FORTUNE_FILE, "r", encoding="utf-8")
fortunes = fp.read().split("%\n")
fp.close()

# Create the package statements
#
log.debug("Creating SQL statements for packages.")
count = 0
for p in list(seen_pkgs.keys()):
    NOW = int(time.time())
    if count % 2 == 0:
        muid = developers[random.randrange(0, len(developers))]
        puid = developers[random.randrange(0, len(developers))]
    else:
        muid = packagemaintainers[random.randrange(0, len(packagemaintainers))]
        puid = packagemaintainers[random.randrange(0, len(packagemaintainers))]
    if count % 20 == 0:  # every so often, there are orphans...
        muid = "NULL"

    uuid = genUID()  # the submitter/user

    if seen_pkgs[p] == pkgbases[p]:
        s = (
            "INSERT INTO PackageBases (ID, Name, FlaggerComment, SubmittedTS, "
            "ModifiedTS, SubmitterUID, MaintainerUID, PackagerUID) VALUES "
            "(%d, '%s', '', %d, %d, %d, %s, %s);\n"
        )
        s = s % (seen_pkgs[p], p, NOW, NOW, uuid, muid, puid)
        out.write(s)

    s = (
        "INSERT INTO Packages (ID, PackageBaseID, Name, Version) VALUES "
        "(%d, %d, '%s', '%s');\n"
    )
    s = s % (seen_pkgs[p], pkgbases[p], p, genVersion())
    out.write(s)

    count += 1

    # create random comments for this package
    #
    num_comments = random.randrange(PKG_CMNTS[0], PKG_CMNTS[1])
    for i in range(0, num_comments):
        now = NOW + random.randrange(400, 86400 * 3)
        s = (
            "INSERT INTO PackageComments (PackageBaseID, UsersID,"
            " Comments, RenderedComment, CommentTS) VALUES (%d, %d, '%s', '', %d);\n"
        )
        s = s % (pkgbases[p], genUID(), genFortune(), now)
        out.write(s)

# Cast votes
utcnow = int(datetime.now(UTC).timestamp())

track_votes = {}
log.debug("Casting votes for packages.")
for u in user_keys:
    num_votes = random.randrange(
        int(len(seen_pkgs) * VOTING[0]), int(max(len(seen_pkgs) * VOTING[1], 1))
    )
    pkgvote = {}
    for v in range(num_votes):
        pkg = random.choice(list(pkgbases.values()))
        if pkg not in pkgvote:
            s = (
                "INSERT INTO PackageVotes (UsersID, PackageBaseID, VoteTS)"
                " VALUES (%d, %d, %d);\n"
            )
            s = s % (seen_users[u], pkg, utcnow)
            pkgvote[pkg] = 1
            if pkg not in track_votes:
                track_votes[pkg] = 0
            track_votes[pkg] += 1
            out.write(s)

# Update statements for package votes
#
for p in list(track_votes.keys()):
    s = "UPDATE PackageBases SET NumVotes = %d WHERE ID = %d;\n"
    s = s % (track_votes[p], p)
    out.write(s)

# Create package dependencies and sources
#
log.debug("Creating statements for package depends/sources.")
# the keys of seen_pkgs are accessed many times by random.choice,
# so the list has to be created outside the loops to keep it efficient
seen_pkgs_keys = list(seen_pkgs.keys())
for p in seen_pkgs_keys:
    num_deps = random.randrange(PKG_DEPS[0], PKG_DEPS[1])
    for i in range(0, num_deps):
        # random probability if its an AUR or official package
        official = random.random() < OFFICIAL_PACKAGE_PROBABILITY
        none_existing = random.random() < NONE_EXISTING_PACKAGE_PROBABILITY
        dep = random.choice(OFFICIAL_PACKAGES if official else seen_pkgs_keys)
        if none_existing:
            dep += "-broken"
        deptype = random.randrange(1, 5)
        if deptype == 4 and random.random() < PKG_OPTS_DESC_PROBABILITY:
            dep_desc = "for " + random.choice(seen_pkgs_keys)
            s = (
                "INSERT INTO PackageDepends(PackageID, DepTypeID, DepName, DepDesc) "
                "VALUES (%d, %d, '%s', '%s');\n"
            )
            s = s % (seen_pkgs[p], deptype, dep, dep_desc)
        else:
            s = (
                "INSERT INTO PackageDepends(PackageID, DepTypeID, DepName) "
                "VALUES (%d, %d, '%s');\n"
            )
            s = s % (seen_pkgs[p], deptype, dep)
        out.write(s)

    num_rels = random.randrange(PKG_RELS[0], PKG_RELS[1])
    for i in range(0, num_rels):
        # make aur packages provide official packages
        official = random.random() < OFFICIAL_PACKAGE_PROBABILITY
        reltype = random.randrange(1, 4)
        rel = random.choice(
            OFFICIAL_PACKAGES if official and reltype == 2 else seen_pkgs_keys
        )
        s = (
            "INSERT INTO PackageRelations(PackageID, RelTypeID, RelName) "
            "VALUES (%d, %d, '%s');\n"
        )
        s = s % (seen_pkgs[p], reltype, rel)
        out.write(s)

    num_sources = random.randrange(PKG_SRC[0], PKG_SRC[1])
    for i in range(num_sources):
        src_file = user_keys[random.randrange(0, len(user_keys))]
        src = "%s%s.%s/%s/%s-%s.tar.gz" % (
            RANDOM_URL[random.randrange(0, len(RANDOM_URL))],
            p,
            RANDOM_TLDS[random.randrange(0, len(RANDOM_TLDS))],
            RANDOM_LOCS[random.randrange(0, len(RANDOM_LOCS))],
            src_file,
            genVersion(),
        )
        s = "INSERT INTO PackageSources(PackageID, Source) VALUES (%d, '%s');\n"
        s = s % (seen_pkgs[p], src)
        out.write(s)

# Create package maintainer proposals
#
log.debug("Creating SQL statements for package maintainer proposals.")
count = 0
for t in range(0, OPEN_PROPOSALS + CLOSE_PROPOSALS):
    now = int(time.time())
    if count < CLOSE_PROPOSALS:
        start = now - random.randrange(3600 * 24 * 7, 3600 * 24 * 21)
        end = now - random.randrange(0, 3600 * 24 * 7)
    else:
        start = now
        end = now + random.randrange(3600 * 24, 3600 * 24 * 7)
    if count % 5 == 0:  # Don't make the vote about anyone once in a while
        user = ""
    else:
        user = user_keys[random.randrange(0, len(user_keys))]
    suid = packagemaintainers[random.randrange(0, len(packagemaintainers))]
    s = (
        "INSERT INTO VoteInfo (Agenda, User, Submitted, End,"
        " Quorum, SubmitterID) VALUES ('%s', '%s', %d, %d, 0.0, %d);\n"
    )
    s = s % (genFortune(), user, start, end, suid)
    out.write(s)
    count += 1

# close output file
#
out.write("COMMIT;\n")
out.write("\n")
out.close()
log.debug("Done.")
