<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include("aur.inc");         # access AUR common functions
include("pkgfuncs.inc");    # use some form of this for i18n support
set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in
html_header();              # print out the HTML header

# Make sure this visitor is logged in
#
if (isset($_COOKIE["AURSID"])) {
	$atype = account_from_sid($_COOKIE["AURSID"]);
} else {
	$atype = "";
}
if (!$atype) {
	print __("You must be logged in before you can edit package information.");
	print "<br />\n";
	html_footer(AUR_VERSION);
	exit();
}

# Must know what package to operate on throughout this entire script
#
if (!$_REQUEST["ID"]) {
	print __("Missing package ID.");
	print "<br />\n";
	html_footer(AUR_VERSION);
}


# Delete a comment for this package
#
if ($_REQUEST["del_Comment"]) {
	if ($_REQUEST["comment_id"]) {
		if (canDeleteComment($_REQUEST["comment_id"], $atype, $_COOKIE["AURSID"])) {
			$dbh = db_connect();
			$uid = uid_from_sid($_COOKIE["AURSID"]);
			$q = "UPDATE PackageComments ";
			$q.= "SET DelUsersID = ".$uid." ";
			$q.= "WHERE ID = ".intval($_REQUEST["comment_id"]);
			db_query($q, $dbh);
			print __("Comment has been deleted.")."<br />\n";
		} else {
			print __("You are not allowed to delete this comment.")."<br />\n";
		}
	} else {
		print __("Missing comment ID.")."<br />\n";
	}
	html_footer(AUR_VERSION);
	exit();
}

# Change package category
#
if ($_REQUEST["change_Category"]) {
	$cat_array = pkgCategories();
	$dbh = db_connect();

	if ($_REQUEST["category_id"]) {
		# Try and set the requested category_id
		#
		if (array_key_exists($_REQUEST["category_id"], $cat_array)) {
			$q = "UPDATE Packages SET CategoryID = ".intval($_REQUEST["category_id"]);
			$q.= " WHERE ID = ".intval($_REQUEST["ID"]);
			db_query($q, $dbh);
			print __("Package category updated.")."<br />\n";

		} else {
			print __("Invalid category ID.")."<br />\n";
		}
	} else {
		# Prompt visitor for new category_id
		#
		$q = "SELECT CategoryID FROM Packages WHERE ID = ".intval($_REQUEST["ID"]);
		$result = db_query($q, $dbh);
		if ($result != NULL) {
			$catid = mysql_fetch_row($result);
		}
		print "<form action='pkgedit.php' method='post'>\n";
		print "<input type='hidden' name='change_Category' value='1'>\n";
		print "<input type='hidden' name='ID' value=\"".$_REQUEST["ID"]."\">\n";
		print __("Select new category").":&nbsp;\n";
		print "<select name='category_id'>\n";
		while (list($id,$cat) = each($cat_array)) {
			print "<option value='".$id."'";
			if ($id == $catid[0]) {
				print " selected";
			}
			print "> ".$cat."</option>\n";
		}
		print "</select>\n";
		print "<br />&nbsp;<br />\n";
		print "<input type='submit' value=\"".__("Submit")."\">\n";
		print "<input type='reset' value=\"".__("Reset")."\">\n";
		print "</form>\n";

	}
	html_footer(AUR_VERSION);
	exit();
}

print __("You've found a bug if you see this....")."<br />\n";

html_footer(AUR_VERSION);

