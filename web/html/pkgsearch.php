<?
include("aur.inc");         # access AUR common functions
include("pkgs.inc");        # package specific functions
include("search_po.inc");   # use some form of this for i18n support
set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in
html_header();              # print out the HTML header
	
# TODO Maybe pkgsearch, pkgvote can be consolidated?  This script can
# provide a search form.  In the results, it can contain a checkbox
# for 'flag out of date', 'vote', 'details' link, and a link to 'pkgmgmnt'.
#
# the results page should have columns for,
# pkg name/ver, location, maintainer, description, O-O-D, Vote, details, mgmnt
#


# get login privileges
#
if (isset($_COOKIE["AURSID"])) {
	# Only logged in users can do stuff
	#
	$atype = account_from_sid($_COOKIE["AURSID"]);
} else {
	$atype = "";
}


if ($atype && $_REQUEST["Action"] == "Something") {
	# do something based on what the user specifies
	#

} elseif ($atype && $_REQUEST["Action"] == "SomethingElse") {
	# do something else based on what the user specifies
	#

} elseif ($_REQUEST["Action"] == "SearchPkgs") {
	# the visitor has requested search options and/or hit the less/more button
	#
	pkg_search_page($_COOKIE["AURSID"], $_REQUEST["L"], $_REQUEST["C"],
			$_REQUEST["K"], $_REQUEST["SB"], $_REQUEST["M"], $_REQUEST["O"],
			$_REQUEST["PP"]);

} else {
	# do the default thing - give the user a search form that they
	# can specify: location, category, maintainer, name, 'my pkgs'
	# and display a list of packages based on no search options.
	#
	pkg_search_page($_COOKIE["AURSID"]);
}


html_footer("\$Id$");
?>
