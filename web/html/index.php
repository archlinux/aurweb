<?
include("index_po.inc");
include("aur.inc");
set_lang();
html_header();


#$dbh = db_connect();
print "Connected...<br>\n";
print "My LANG is: " . $LANG . "<br>\n";


html_footer("\$Id$");
?>
