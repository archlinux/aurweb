<?php

# This template shows how a front page script is commonly coded.

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include("aur.inc");         # access AUR common functions
set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in
html_header();              # print out the HTML header


# Any text you print out to the visitor, use the __() function
# for i18n support. See web/lib/translator.inc for more info.
#
print __("Hi, this is worth reading!")."<br />\n";


html_footer(AUR_VERSION);

