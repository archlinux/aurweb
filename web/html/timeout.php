<?
include("timeout_po.inc");
include("aur.inc");
set_lang();
html_header();

print __("Your session has timed out.  You must log in again.");
print "<p>\n";
print __("Click on the Home link above to log in.");
print "</p>\n";

html_footer("\$Id$");
?>
