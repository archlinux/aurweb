<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../lang');

include("aur.inc");         # access AUR common functions
include("pkgfuncs.inc");    # use some form of this for i18n support
include("pkgedit_po.inc");  # i18n translations for this script
set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in
html_header();              # print out the HTML header
$svn_idstr = "\$Id$";

$DBUG = 0;
if ($DBUG) {
	print "<pre>\n";
	print_r($_REQUEST);
	print "</pre>\n";
}

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
	pkgdetails_link($_REQUEST["ID"]);
	html_footer(AUR_VERSION);
	exit();
}

# Add a comment to this package
#
if ($_REQUEST["add_Comment"]) {
	if ($_REQUEST["comment"]) {
		# Insert the comment
		#
		$dbh = db_connect();
		$q = "INSERT INTO PackageComments ";
		$q.= "(PackageID, UsersID, Comments, CommentTS) VALUES (";
		$q.= intval($_REQUEST["ID"]).", ".uid_from_sid($_COOKIE["AURSID"]) . ", ";
		$q.= "'".mysql_real_escape_string($_REQUEST["comment"])."', ";
		$q.= "UNIX_TIMESTAMP())";
		db_query($q, $dbh);
		print __("Comment has been added.")."<br />&nbsp;<br />\n";
		pkgdetails_link($_REQUEST["ID"]);

		# Send email notifications
		#
		$q = "SELECT CommentNotify.*, Users.Email ";
		$q.= "FROM CommentNotify, Users ";
		$q.= "WHERE Users.ID = CommentNotify.UserID ";
		$q.= "AND CommentNotify.UserID != ".uid_from_sid($_COOKIE["AURSID"])." ";
		$q.= "AND CommentNotify.PkgID = ".intval($_REQUEST["ID"]);
		$result = db_query($q, $dbh);
		$bcc = array();
		if (mysql_num_rows($result)) {
			while ($row = mysql_fetch_assoc($result)) {
				array_push($bcc, $row['Email']);
			}
			$q = "SELECT Packages.Name ";
			$q.= "FROM Packages ";
			$q.= "WHERE Packages.ID = ".intval($_REQUEST["ID"]);
			$result = db_query($q, $dbh);
			$row = mysql_fetch_assoc($result);
			#TODO: native language emails for users, based on their prefs
			# Simply making these strings translatable won't work, users would be
			# getting emails in the language that the user who posted the comment was in
			$body = "A comment has been added to ".$row['Name'].", you may view it at:\nhttp://aur.archlinux.org/packages.php?do_Details=1&ID=".$_REQUEST["ID"]."\n\n\n---\nYou received this e-mail because you chose to recieve notifications of new comments on this package, if you no longer wish to recieve notifications about this package, please go the the above package page and click the UnNotify.";
			$body = wordwrap($body, 70);
			$bcc = implode(', ', $bcc);
			$headers = "Bcc: $bcc\nReply-to: nobody@archlinux.org\nFrom:aur-notify@archlinux.org\nX-Mailer: PHP\nX-MimeOLE: Produced By AUR\n";
			@mail(' ', "AUR Comment Notification for ".$row['Name'], $body, $headers);
		}

	} else {
		# Prompt visitor for comment
		#
		print "<div align='center'>\n";
		print "<form action='/pkgedit.php' method='post'>\n";
		print "<input type='hidden' name='add_Comment' value='1'>\n";
		print "<input type='hidden' name='ID' value=\"".$_REQUEST["ID"]."\">\n";
		print __("Enter your comment below.")."<br />&nbsp;<br />\n";
		print "<textarea name='comment' rows='10' cols='50'></textarea>\n";
		print "<br />&nbsp;<br />\n";
		print "<input type='submit' value=\"".__("Submit")."\">\n";
		print "<input type='reset' value=\"".__("Reset")."\">\n";
		print "</form>\n";
		print "</div>\n";
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
		pkgdetails_link($_REQUEST["ID"]);

	} else {
		# Prompt visitor for new category_id
		#
		$q = "SELECT CategoryID FROM Packages WHERE ID = ".intval($_REQUEST["ID"]);
		$result = db_query($q, $dbh);
		if ($result != NULL) {
			$catid = mysql_fetch_row($result);
		}
		print "<form action='/pkgedit.php' method='post'>\n";
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

html_footer(AUR_VERSION);   # Use the $Id$ keyword
                           # NOTE: when checking in a new file, use
                           # 'svn propset svn:keywords "Id" filename.php'
                           # to tell svn to expand the "Id" keyword.

# vim: ts=2 sw=2 noet ft=php
?>
