<?
# This is a sample script to demonstrate how the AUR will
# handle i18n.  Note:  When the PHP script is finished, and
# has the proper include file (see below), and the __()
# function has been used (see below), use the web/utils/genpopo
# script to parse the PHP script and pull out the text
# that requires translation and puts the mapping into the
# include file.
#

# Each AUR PHP script that requires i18n support, needs to
# define an 'xxx_po.inc' file where the i18n mapping will
# reside.
#
include("test_po.inc");


# Use the __() function to identify text that requires
# translation to other languages.  The examples below
# show how to use %-substitution.
#
print "<html><body bgcolor='white'>\n";

print "<p>\n";
print __("Select your language here: %h%s%h, %h%s%h, %h%s%h, %h%s%h.",
		array("<a href='".$_SERVER['PHP_SELF']."?LANG=en'>","English","</a>",
		"<a href='".$_SERVER['PHP_SELF']."?LANG=es'>","Español","</a>",
		"<a href='".$_SERVER['PHP_SELF']."?LANG=de'>","Deutsch","</a>",
		"<a href='".$_SERVER['PHP_SELF']."?LANG=fr'>","Français","</a>"));
print "</p>\n";

print "<p>\n";
print __("My current language tag is: '%s'.", array($LANG));
print "</p>\n";

print "<ul>\n";
print __("Hello, world!")."<br/>\n";
print __("Hello, again!")."<br/>\n";
print "</ul>\n";
print "</body>\n</html>";

?>
