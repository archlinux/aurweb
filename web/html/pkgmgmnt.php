<?
include("aur.inc");         # access AUR common functions
include("mgmnt_po.inc");    # use some form of this for i18n support
set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in
html_header();              # print out the HTML header


# Any text you print out to the visitor, use the __() function
# for i18n support.  See 'testpo.php' for more details.
#
print __("Under construction...")."<br/>\n";


html_footer("\$Id$");
?>
