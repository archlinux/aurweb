aurweb
======

aurweb is a hosting platform for the Arch User Repository (AUR), a collection
of packaging scripts that are created and submitted by the Arch Linux
community. The scripts contained in the repository can be built using `makepkg`
and installed using the Arch Linux package manager `pacman`.

The aurweb project includes

* A web interface to search for packaging scripts and display package details.
* An SSH/Git interface to submit and update packages and package meta data.
* Community features such as comments, votes, package flagging and requests.
* Editing/deletion of packages and accounts by Trusted Users and Developers.
* Area for Trusted Users to post AUR-related proposals and vote on them.

Directory Layout
----------------

* `aurweb`: aurweb Python modules, Git interface and maintenance scripts
* `conf`: configuration and configuration templates
* `static`: static resource files
* `templates`: jinja2 template collection
* `doc`: project documentation
* `po`: translation files for strings in the aurweb interface
* `schema`: schema for the SQL database
* `test`: test suite and test cases
* `upgrading`: instructions for upgrading setups from one release to another
* `web`: PHP-based web interface for the AUR

Links
-----

* The repository is hosted at git://git.archlinux.org/aurweb.git -- see
  doc/CodingGuidelines for information on the patch submission process.

* Bugs can (and should) be submitted to the aurweb bug tracker:
  https://bugs.archlinux.org/index.php?project=2

* Questions, comments, and patches related to aurweb can be sent to the AUR
  development mailing list: aur-dev@archlinux.org -- mailing list archives:
  https://mailman.archlinux.org/mailman/listinfo/aur-dev

Translations
------------

Translations are welcome via our Transifex project at
https://www.transifex.com/lfleischer/aurweb; see `doc/i18n.txt` for details.

![Transifex](https://www.transifex.com/projects/p/aurweb/chart/image_png)

Testing
-------

See [test/README.md](test/README.md) for details on dependencies and testing.
