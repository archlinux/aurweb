<?
include("aur.inc");         # access AUR common functions
include("mgmnt_po.inc");    # use some form of this for i18n support
set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in
html_header();              # print out the HTML header


# vistor has requested package management for a specific package
#
print __("Manage package ID: %s", array($_REQUEST["ID"])) . "<br />\n";

# NOTE: managing an orphaned package will automatically force adoption
#


html_footer("\$Id$");
# vim: ts=2 sw=2 noet ft=php
?>
