<?
include("aur.inc");         # access AUR common functions
include("logout_po.inc");   # use some form of this for i18n support
set_lang();                 # this sets up the visitor's language

# if they've got a cookie, log them out - need to do this before
# sending any HTML output.
#
if (isset($_COOKIE["AURSID"])) {
	$q = "DELETE FROM Sessions WHERE SessionID = '";
	$q.= mysql_escape_string($_COOKIE["AURSID"]) . "'";
	setcookie("AURSID", "", time() - (60*60*24*30), "/");
}

html_header();              # print out the HTML header
print __("You have been successfully logged out.")."<br/>\n";


html_footer("\$Id$");
?>
