<?
include("aur.inc");         # access AUR common functions
include("pkgfuncs.inc");    # package specific functions
include("search_po.inc");   # use some form of this for i18n support
set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in
html_header();              # print out the HTML header
	

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

		# After flagging, show the search page again (or maybe print out
		# a message and give the user a link to resume where they were
		# in the search
		#
		pkg_search_page($_COOKIE["AURSID"]);
				
	}


} elseif (isset($_REQUEST["do_Disown"])) {
	if ($atype == "User" || $atype == "") {
		print __("You do not have access to disown packages.");
		print "<br />\n";

	} else {
		# Disown the packages in $ids array
		#
		print "disowning<br />\n";

		# After disowning, show the search page again (or maybe print out
		# a message and give the user a link to resume where they were
		# in the search
		#
		pkg_search_page($_COOKIE["AURSID"]);

	}


} elseif (isset($_REQUEST["do_Adopt"])) {
	if ($atype == "User" || $atype == "") {
		print __("You do not have access to adopt packages.");
		print "<br />\n";

	} else {
		# Adopt the packages in $ids array
		#
		print "adopting<br />\n";

		# After adopting, show the search page again (or maybe print out
		# a message and give the user a link to resume where they were
		# in the search
		#
		pkg_search_page($_COOKIE["AURSID"]);

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

		# After voting, show the search page again (or maybe print out
		# a message and give the user a link to resume where they were
		# in the search
		#
		pkg_search_page($_COOKIE["AURSID"]);

	}


} elseif (isset($_REQUEST["do_Details"])) {
	# give a link to 'manage', and another to return to search
	# results.
	#
	print "details for package<br />\n";


} else {
	# do_More/do_Less/do_Search/do_MyPackages - just do a search
	#
	pkg_search_page($_COOKIE["AURSID"]);

}

html_footer("\$Id$");
?>
