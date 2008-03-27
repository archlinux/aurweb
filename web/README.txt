Setup on ArchLinux:
===================
1) Install Apache, MySQL, PHP, and git 
  # pacman -Sy apache mysql php git 

2) Set a local 'hostname' of 'aur'
 - Edit /etc/hosts and append 'aur' to loopback address
   127.0.0.1    localhost aur

3) Configure Apache

 - Edit /etc/httpd/conf/httpd.conf and make sure that PHP
   support is enabled by uncommenting the LoadModule line
   that specifies the PHP module.

 - Also append the following snippet to enable the aur
   Virtual Host (Replace MYUSER with your username).

   <VirtualHost aur:80>
   Servername    aur
   DocumentRoot    /home/MYUSER/aur/web/html
   ErrorLog    /var/log/httpd/aur-error.log
   CustomLog   /var/log/httpd/aur-access.log combined
     <Directory /home/MYUSER/aur/web/html>
       Options Indexes FollowSymLinks
       AllowOverride All
     </Directory>
   </VirtualHost>

4) Configure PHP
   Make sure you have mysql and json enabled in PHP

 - Edit php.ini and uncomment/add these lines:
   extension=mysql.so
   extension=json.so

5) Clone the AUR project (using the MYUSER from above)
   $ cd
   $ git clone http://projects.archlinux.org/git/aur.git

6) Configure MySQL
 - Connect to the mysql client
   # mysql -uroot

 - Issue the following commands to the mysql client
   mysql> CREATE DATABASE AUR;
   mysql> GRANT ALL PRIVILEGES ON AUR.* to aur@localhost
        > identified by 'aur';
   mysql> FLUSH PRIVILEGES;
   mysql> quit

 - Load the schema file
   # mysql -uaur -p AUR < ~/aur/support/schema/aur-schema.sql
   (give password 'aur' at the prompt)

 - Optionally load some test data for development purposes.
   # bzcat ~/aur/support/schema/dummy-data.sql.bz2 | mysql -uaur -p AUR
   (give password 'aur' at the prompt)

7) Copy the config.inc.proto file to config.inc. Modify as needed.
   cd ~/aur/web/lib/
   cp config.inc.profo config.inc

8) Point your browser to http://aur


Web Interface:
==============

Directory Layout:
-----------------
./html        - DocumentRoot for AUR, where the PHP scripts live.
./html/css    - CSS stylesheets
./html/images - Any AUR images live here.
./lib         - Supporting PHP include files.  Access denied to Apache.
./template    - Where most of the html markup resides and minimal
                amount of PHP scripting.


Scripts:
--------
- lib/aur.inc
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

- html/packages.php
  PHP script to search the package database.  It should support
  searching by location ("unsupported", "AUR", "extra"), name,
  category, maintainer, popularity, etc.  It should resemble the
  packages.php script on archlinux.org.  A checkbox should be
  included next to each package to allow users to flag a package
  out of date, adopt it, and vote for it (and reverse operations).

- html/pkgmgmnt.php
  This script is not accessed directly, but is invoked when a
  visitor clicks the 'manage' link from the 'packages.php' script.
  The user can edit the package information stored in the database
  such as the description, url, category, and location (a TU can move
  it to/from "unsupported" and the "AUR").  This is where TUs can
  adopt packages that are in the "unsupported" area.

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

