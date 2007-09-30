<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../lang');

include("aur.inc");         # access AUR common functions
include("pkgfuncs_po.inc"); # Add to handle the i18n of My Packages
include("logout_po.inc");   # use some form of this for i18n support
set_lang();                 # this sets up the visitor's language

# if they've got a cookie, log them out - need to do this before
# sending any HTML output.
#
if (isset($_COOKIE["AURSID"])) {
	$dbh = db_connect();
	$q = "DELETE FROM Sessions WHERE SessionID = '";
	$q.= mysql_real_escape_string($_COOKIE["AURSID"]) . "'";
	db_query($q, $dbh);
	setcookie("AURSID", "", time() - (60*60*24*30), "/");
	setcookie("AURLANG", "", time() - (60*60*24*30), "/");
}

header('Location: index.php');
exit;

html_footer("\$Id$");
# vim: ts=2 sw=2 noet ft=php
?>
