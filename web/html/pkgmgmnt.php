<?
include("aur.inc");         # access AUR common functions
include("mgmnt_po.inc");    # use some form of this for i18n support
set_lang();                 # this sets up the visitor's language
html_header();              # print out the HTML header


# Any text you print out to the visitor, use the __() function
# for i18n support.  See 'testpo.php' for more details.
#
print __("Under construction...")."<br/>\n";


html_footer("\$Id$");      # Use the $Id$ keyword
                           # NOTE: when checking in a new file, use
                           # 'svn propset svn:keywords "Id" filename.php'
                           # to tell svn to expand the "Id" keyword.
?>
