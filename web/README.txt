Web Interface:
==============

Directory Layout:
-----------------
./html        - DocumentRoot for AUR, where the PHP scripts live.
./html/css    - CSS stylesheets
./html/images - Any AUR images live here.
./lib         - Supporting PHP include files.  Access denied to Apache.


Scripts:
--------
- lib/funcs.inc
  This is where we can stick functions that can be shared
  between the various scripts.  Also a good place to put the
  MySQL authentication variables since it should live outside
  the DocumentRoot.

- html/login.php (probably index.php)
  PHP script to handle logging users into the AUR web site.  It
  authenticates using the email address and a password against
  the Users table.  Once authenticated, a session id is generated
  and stored in the Sessions table and sent as a cookie to the
  user's browser.

- html/logout.php
  PHP script to logout.  It clears the session id from the
  Sessions table and unsets the cookie.

- html/account.php
  PHP script to handle registering for a new account.  It prompts
  the visitor for account information: Email, password, real name,
  irc nick.  The info is recorded in the Users table.  Perhaps later,
  we can add a preferences field that allows the user to request to
  be notified when new packages are submitted so that they can cast
  votes for them?

  If a TU is logged into the system, they can edit accounts and set
  the account type (regular user or TU).  If a Dev is logged in, they
  can also set the account type to Dev.  TUs and Devs are able to
  delete accounts.  If an account is deleted, all "Unsupported"
  packages are orphaned (the Users.ID field in the UnsupportedPackages
  table is set to Null).

- html/pkgsearch.php
  PHP script to search the package database.  It should support
  searching by location ("unsupported", "AUR", "extra"), name,
  category, maintainer, popularity, etc.  It should resemble the
  packages.php script on archlinux.org.  A checkbox should be
  included next to each package to allow users to flag a package
  out of date.

- html/pkgvote.php
  The PHP script that handles voting for packages.  It works like
  the search script above to provide a list of packages (maybe by
  location only?) with a checkbox for the user to register their
  'yes' vote.  It should probably only list 50-ish packages per page
  and allow the user to vote a page at a time.  Each page contains a
  'Continue' button to advance to the next list of packages.  At the
  final page, a summary is presented with a 'Cast Vote' button.  Once
  the vote is cast, the PackageVotes table is first cleared for that
  User and then all new entries are added for the new vote (this will
  be easier than trying to figure out if the vote has changed for a
  particular package).

- html/pkgmgmnt.php
  The PHP script for managing packages.  It provides a list of
  packages under the management of the logged in user (normal or
  TU).  The user can edit the package information stored in the
  database such as the description, url, category, and location
  (a TU can move it to/from "unsupported" and the "AUR").  This
  is where TUs can adopt packages that are in the "unsupported"
  area.

- html/pkgsubmit.php
  This is the PHP script that allows users to upload a new package.
  The package format will be a tgz containing the PKGBUILD,
  scriptlets, and patches necessary to build the package from
  source.  Initially, the user submitting the package can select
  its category (network, devel, etc) but that can be modified
  later by the adopting TU.  The script makes appropriate entries
  into the database (and perhaps notifies interested users of the
  new package - see question above).


New terms/definitions:
======================
TU - No change (trusted by the community, if anyone asks what trust
     means)
TUR - renamed to Arch User-community Repo (AUR) (so we can use -u for
      versions)
Incoming - renamed to "Unsupported"

