<?
include("aur.inc");         # access AUR common functions
include("index_po.inc");    # use some form of this for i18n support
html_header();              # print out the HTML header


# Any text you print out to the visitor, use the _() function
# for i18n support.  See 'testpo.php' for more details.
#
print _("Hi, this is worth reading!")."<br/>\n";


html_footer("\$Id$");      # Use the $Id$ keyword
                           # NOTE: when checking in a new file, use the
                           # 'svn propset svn:keywords "Id" filename.php
                           # to tell svn to expand the "Id" keyword.
?>
