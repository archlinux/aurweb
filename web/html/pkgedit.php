<?
include("aur.inc");         # access AUR common functions
include("pkgfuncs.inc");    # use some form of this for i18n support
set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in
html_header();              # print out the HTML header


$DBUG = 0;
if ($DBUG) {
	print "<pre>\n";
	print_r($_REQUEST);
	print "</pre>\n";
}

if (isset($_COOKIE["AURSID"])) {
	$atype = account_from_sid($_COOKIE["AURSID"]);
} else {
	$atype = "";
}

if (!$atype) {
	print __("You must be logged in before you can edit package information.");
	print "<br />\n";
} else {
	if (!$_REQUEST["ID"]) {
		print __("Missing package ID.");
		print "<br />\n";
	} else {

		# Main script processing here... basic error checking done.
		#
		if ($_REQUEST["add_Comment"]) {
			if ($_REQUEST["comment"]) {
			} else {
			}
		}

	}
}

html_footer("\$Id$");      # Use the $Id$ keyword
                           # NOTE: when checking in a new file, use
                           # 'svn propset svn:keywords "Id" filename.php'
                           # to tell svn to expand the "Id" keyword.

# vim: ts=2 sw=2 et ft=php
?>
