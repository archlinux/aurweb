This is the finalized draft of the project requirements for the
new Arch package submittal process.  AUR (Arch User-community Repo).
The sub-directories contain more specific implementation notes
for each component of the project.


Requirements:
-------------
1) User accounts (users, TUs)
 - Create account. (email address required)
 - Update account (change password/email address)
 - Log in/out

2) Search for packages (public)
 - needs knowledge of ALL pkgs (OfficalRepos/AUR/Unsupported).  This
   should be easy enough if this site lives on the same machine as
   the current package database (dragon?), or is allowed to query
   the db.
 - Display official repo (current/extra) a package lives in.

3) Manual voting (requires user acct)
 - reset/clear all votes (for starting over, this can be added later
   if there is any demand for it)

4) Package Management
 - A package can be submitted by anyone (as long as they create
   an account with a valid email address on the web site).  From
   there, a TU inspects the package and works with the submitter
   to resolve any bugs/issues.  Once approved, the TU can place the
   package in the AUR.  From there, if the package is popular enough
   (or deemed necessary), a developer can move the package from the
   AUR to extra/current/etc.  A developer can also downgrade a
   package from extra/current/etc to the AUR.
 - The person that uploaded the new package can make changes to
   it before it has been added to the AUR.
 - TUs need to be able to purge packages in "Unsupported" if the
   package is no longer maintained and there is no interest in
   keeping it.
 - Packages in the AUR/Unsupported need some sort of 'flag out of
   date' support.
 - Interested users can download the package from "Unsupported"
   and build/install it by hand.
 - Provide a separate installation of flyspray for tracking bugs
   for packages living in the AUR.  All bugs should be resolved
   in either flyspray (AUR/official) prior to a package being
   promoted/demoted.

5) Reports
 - package popularity by number of votes

6) Wiki Docs (UID/GID db, provides db, irc nicks/names TUs/devs)
 - Move the appropriate dev wiki pages to the new system's
   wiki area.  The devs will just need to consult the UID/GID
   list from the new system site rather than our own wiki.

7) Submitting 'new' packages by users.  Initially start with
   a simple web upload page where users submit a tgz containing
   the PKGBUILD, scriptlets, patches, etc.  The script will
   unpack the tgz in an appropriate location and update the
   backend database to 'register' the pacakge.

8) TU package management
 - A TU adopts a package from "Unsupported" and that shows users
   and other TUs that the package is being reviewed.
 - When the TU is ready to move the package to the AUR, they
   use a custom utility/script that allows them to upload the
   pkg.tar.gz (web uploads are inadequate for this process).
   The upload utility/script has a server counterpart that
   performs TU authentication and updates the database.
 - A cronjob on the server can handle the new AUR package,
   update the database, and rebuild the AUR sync db, and send
   email notices to the TU about errors if any occur.
 - The TUs should also be able to demote a package from the
   AUR via the web interface.
 - TUs will use cvs/svn interface (just like devs) to pull
   down the PKGBUILD tree.  This tree should reflect the same
   layout as extra for easier package migration.  They make
   changes to their local copy, test, and then commit.  They
   use the xfer utility to upload the binary package to the
   server.  No shell access is required.


Automated Voting Tool (similar to ArchStats client)
=====================

Requirements:
-------------
  1) Name of tool is 'pkgvote'

  2) Requires registered account on web - email address not required

  3) Casts 'yes' votes for all installed packages (except itself?)

Implementation:
---------------
  A statically compiled C program that gathers the list of installed
  packages and casts the vote to the web site.  Very similar to the
  way that ArchStats works now.  When making the HTTP Post, it adds
  a custom HEADER that the PHP script(s) can detect to know that it
  is receiving a vote from a 'pkgvote' client.  If the PHP script
  does not see the special HEADER, it assumes it is a web browser
  and gives the user HTML output.

  Once installed, the user edits the config file and supplies their
  username/password.  If no username/password exists in the config
  file when it starts, it spits out an error message and exits.

