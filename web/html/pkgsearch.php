<?
include("aur.inc");         # access AUR common functions
include("pkgfuncs.inc");    # package specific functions
include("search_po.inc");   # use some form of this for i18n support
set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in
html_header();              # print out the HTML header

# define variables used during pkgsearch
#
$pkgsearch_vars = array("O", "L", "C", "K", "SB", "PP", "do_MyPackages");

	
# get login privileges
#
if (isset($_COOKIE["AURSID"])) {
	# Only logged in users can do stuff
	#
	$atype = account_from_sid($_COOKIE["AURSID"]);
} else {
	$atype = "";
}

# grab the list of Package IDs to be operated on
#
isset($_REQUEST["IDs"]) ? $ids = $_REQUEST["IDs"] : $ids = array();


# determine what button the visitor clicked
#
if (isset($_REQUEST["do_Flag"])) {
	if (!$atype) {
		print __("You must be logged in before you can flag packages.");
		print "<br />\n";

	} else {
		# Flag the packages in $ids array, and unflag any other
		# packages listed in $_REQUEST["All_IDs"]
		#
		print "flagging<br />\n";

		pkgsearch_results_link();
				
	}


} elseif (isset($_REQUEST["do_Disown"])) {
	if (!$atype) {
		print __("You must be logged in before you can disown packages.");
		print "<br />\n";

	} else {
		# Disown the packages in $ids array
		#
		print "disowning<br />\n";

		pkgsearch_results_link();

	}


} elseif (isset($_REQUEST["do_Adopt"])) {
	if (!$atype) {
		print __("You must be logged in before you can adopt packages.");
		print "<br />\n";

	} else {
		# Adopt the packages in $ids array
		#
		print "adopting<br />\n";

		pkgsearch_results_link();

	}


} elseif (isset($_REQUEST["do_Vote"])) {
	if (!$atype) {
		print __("You must be logged in before you can vote for packages.");
		print "<br />\n";

	} else {
		# vote on the packages in $ids array.  'unvote' for any packages
		# listed in the $_REQUEST["All_IDs"] array.
		#
		print "voting<br />\n";

		pkgsearch_results_link();

	}


} elseif (isset($_REQUEST["do_Details"])) {

	if (!isset($_REQUEST["ID"]) || !intval($_REQUEST["ID"])) {
		print __("Error trying to retrieve package details.")."<br />\n";
		
	} else {
		package_details($_REQUEST["ID"]);
	}

	print "<br />\n";
	pkgsearch_results_link();
	print "</center>\n";
	print "<br />\n";


} else {
	# do_More/do_Less/do_Search/do_MyPackages - just do a search
	#
	pkg_search_page($_COOKIE["AURSID"]);

}

html_footer("\$Id$");
?>
