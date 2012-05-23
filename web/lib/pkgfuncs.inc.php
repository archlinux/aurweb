<?php
include_once("config.inc.php");

# Make sure this visitor can delete the requested package comment
# They can delete if they were the comment submitter, or if they are a TU/Dev
#
function canDeleteComment($comment_id=0, $atype="", $uid=0, $dbh=NULL) {
	if ($atype == "Trusted User" || $atype == "Developer") {
		# A TU/Dev can delete any comment
		return TRUE;
	}
	if(!$dbh) {
		$dbh = db_connect();
	}
	$q = "SELECT COUNT(ID) AS CNT ";
	$q.= "FROM PackageComments ";
	$q.= "WHERE ID = " . intval($comment_id);
	$q.= " AND UsersID = " . $uid;
	$result = db_query($q, $dbh);
	if ($result != NULL) {
		$row = mysql_fetch_assoc($result);
		if ($row['CNT'] > 0) {
			return TRUE;
		}
	}
	return FALSE;
}

# Make sure this visitor can delete the requested package comment
# They can delete if they were the comment submitter, or if they are a TU/Dev
#
function canDeleteCommentArray($comment, $atype="", $uid=0) {
	if ($atype == "Trusted User" || $atype == "Developer") {
		# A TU/Dev can delete any comment
		return TRUE;
	} else if ($comment['UsersID'] == $uid) {
		# User's own comment
		return TRUE;
	}
	return FALSE;
}

# see if this Users.ID can manage the package
#
function canManagePackage($uid=0,$AURMUID=0, $MUID=0, $SUID=0, $managed=0) {
	if (!$uid) {return 0;}

	# The uid of the TU/Dev that manages the package
	#
	if ($uid == $AURMUID) {return 1;}

	# If the package isn't maintained by a TU/Dev, is this the user-maintainer?
	#
	if ($uid == $MUID && !$managed) {return 1;}

	# If the package isn't maintained by a TU/Dev, is this the user-submitter?
	#
	if ($uid == $SUID && !$managed) {return 1;}

	# otherwise, no right to manage this package
	#
	return 0;
}

# Check if the current user can submit blacklisted packages.
#
function canSubmitBlacklisted($atype = "") {
	if ($atype == "Trusted User" || $atype == "Developer") {
		# Only TUs/Devs can submit blacklisted packages.
		return TRUE;
	}
	else {
		return FALSE;
	}
}

# grab the current list of PackageCategories
#
function pkgCategories($dbh=NULL) {
	$cats = array();
	if(!$dbh) {
		$dbh = db_connect();
	}
	$q = "SELECT * FROM PackageCategories WHERE ID != 1 ";
	$q.= "ORDER BY Category ASC";
	$result = db_query($q, $dbh);
	if ($result) {
		while ($row = mysql_fetch_row($result)) {
			$cats[$row[0]] = $row[1];
		}
	}
	return $cats;
}

# check to see if the package name exists
#
function pkgid_from_name($name="", $dbh=NULL) {
	if (!$name) {return NULL;}
	if(!$dbh) {
		$dbh = db_connect();
	}
	$q = "SELECT ID FROM Packages ";
	$q.= "WHERE Name = '".db_escape_string($name)."' ";
	$result = db_query($q, $dbh);
	if (!$result) {return NULL;}
	$row = mysql_fetch_row($result);
	return $row[0];
}

# grab package dependencies
#
function package_dependencies($pkgid, $dbh=NULL) {
	$deps = array();
	$pkgid = intval($pkgid);
	if ($pkgid > 0) {
		if(!$dbh) {
			$dbh = db_connect();
		}
		$q = "SELECT pd.DepName, pd.DepCondition, p.ID FROM PackageDepends pd ";
		$q.= "LEFT JOIN Packages p ON pd.DepName = p.Name ";
		$q.= "WHERE pd.PackageID = ". $pkgid . " ";
		$q.= "ORDER BY pd.DepName";
		$result = db_query($q, $dbh);
		if (!$result) {return array();}
		while ($row = mysql_fetch_row($result)) {
			$deps[] = $row;
		}
	}
	return $deps;
}

function package_required($name="", $dbh=NULL) {
	$deps = array();
	if ($name != "") {
		if(!$dbh) {
			$dbh = db_connect();
		}
		$q = "SELECT p.Name, PackageID FROM PackageDepends pd ";
		$q.= "JOIN Packages p ON pd.PackageID = p.ID ";
		$q.= "WHERE DepName = '".db_escape_string($name)."' ";
		$q.= "ORDER BY p.Name";
		$result = db_query($q, $dbh);
		if (!$result) {return array();}
		while ($row = mysql_fetch_row($result)) {
			$deps[] = $row;
		}
	}
	return $deps;
}

# Return the number of comments for a specified package
function package_comments_count($pkgid, $dbh=NULL) {
	$pkgid = intval($pkgid);
	if ($pkgid > 0) {
		if(!$dbh) {
			$dbh = db_connect();
		}
		$q = "SELECT COUNT(*) FROM PackageComments ";
		$q.= "WHERE PackageID = " . $pkgid;
		$q.= " AND DelUsersID IS NULL";
	}
	$result = db_query($q, $dbh);

	if (!$result) {
		return;
	}

	return mysql_result($result, 0);
}

# Return an array of package comments
function package_comments($pkgid, $dbh=NULL) {
	$comments = array();
	$pkgid = intval($pkgid);
	if ($pkgid > 0) {
		if(!$dbh) {
			$dbh = db_connect();
		}
		$q = "SELECT PackageComments.ID, UserName, UsersID, Comments, CommentTS ";
		$q.= "FROM PackageComments, Users ";
		$q.= "WHERE PackageComments.UsersID = Users.ID";
		$q.= " AND PackageID = " . $pkgid;
		$q.= " AND DelUsersID IS NULL"; # only display non-deleted comments
		$q.= " ORDER BY CommentTS DESC";

		if (!isset($_GET['comments'])) {
			$q.= " LIMIT 10";
		}

		$result = db_query($q, $dbh);

		if (!$result) {
			return;
		}

		while ($row = mysql_fetch_assoc($result)) {
			$comments[] = $row;
		}
	}
	return $comments;
}

# grab package sources
#
function package_sources($pkgid, $dbh=NULL) {
	$sources = array();
	$pkgid = intval($pkgid);
	if ($pkgid > 0) {
		if(!$dbh) {
			$dbh = db_connect();
		}
		$q = "SELECT Source FROM PackageSources ";
		$q.= "WHERE PackageID = " . $pkgid;
		$q.= " ORDER BY Source";
		$result = db_query($q, $dbh);
		if (!$result) {return array();}
		while ($row = mysql_fetch_row($result)) {
			$sources[] = $row[0];
		}
	}
	return $sources;
}


# grab array of Package.IDs that I've voted for: $pkgs[1234] = 1, ...
#
function pkgvotes_from_sid($sid="", $dbh=NULL) {
	$pkgs = array();
	if (!$sid) {return $pkgs;}
	if(!$dbh) {
		$dbh = db_connect();
	}
	$q = "SELECT PackageID ";
	$q.= "FROM PackageVotes, Users, Sessions ";
	$q.= "WHERE Users.ID = Sessions.UsersID ";
	$q.= "AND Users.ID = PackageVotes.UsersID ";
	$q.= "AND Sessions.SessionID = '".db_escape_string($sid)."'";
	$result = db_query($q, $dbh);
	if ($result) {
		while ($row = mysql_fetch_row($result)) {
			$pkgs[$row[0]] = 1;
		}
	}
	return $pkgs;
}

# array of package ids that you're being notified for
# *yoink*
#
function pkgnotify_from_sid($sid="", $dbh=NULL) {
	$pkgs = array();
	if (!$sid) {return $pkgs;}
	if(!$dbh) {
		$dbh = db_connect();
	}
	$q = "SELECT PkgID ";
	$q.= "FROM CommentNotify, Users, Sessions ";
	$q.= "WHERE Users.ID = Sessions.UsersID ";
	$q.= "AND Users.ID = CommentNotify.UserID ";
	$q.= "AND Sessions.SessionID = '".db_escape_string($sid)."'";
	$result = db_query($q, $dbh);
	if ($result) {
		while ($row = mysql_fetch_row($result)) {
			$pkgs[$row[0]] = 1;
		}
	}
	return $pkgs;
}

# get name of package based on pkgid
#
function pkgname_from_id($pkgids, $dbh=NULL) {
	if (is_array($pkgids)) {
		$pkgids = sanitize_ids($pkgids);
		$names = array();
		if(!$dbh) {
			$dbh = db_connect();
		}
		$q = "SELECT Name FROM Packages WHERE ID IN (" .
			implode(",", $pkgids) . ")";
		$result = db_query($q, $dbh);
		if (mysql_num_rows($result) > 0) {
			while ($row = mysql_fetch_assoc($result)) {
				$names[] = $row['Name'];
			}
		}
		return $names;
	}
	elseif ($pkgids > 0) {
		if(!$dbh) {
			$dbh = db_connect();
		}
		$q = "SELECT Name FROM Packages WHERE ID = " . $pkgids;
		$result = db_query($q, $dbh);
		if (mysql_num_rows($result) > 0) {
			$name = mysql_result($result, 0);
		}
		return $name;
	}
	else {
		return NULL;
	}
}

# Check if a package name is blacklisted.
#
function pkgname_is_blacklisted($name, $dbh=NULL) {
	if(!$dbh) {
		$dbh = db_connect();
	}
	$q = "SELECT COUNT(*) FROM PackageBlacklist WHERE Name = '" . db_escape_string($name) . "'";
	$result = db_query($q, $dbh);

	if (!$result) return false;
	return (mysql_result($result, 0) > 0);
}

# display package details
#
function package_details($id=0, $SID="", $dbh=NULL) {
	global $AUR_LOCATION;

	if(!$dbh) {
		$dbh = db_connect();
	}

	$q = "SELECT Packages.*,Category ";
	$q.= "FROM Packages,PackageCategories ";
	$q.= "WHERE Packages.CategoryID = PackageCategories.ID ";
	$q.= "AND Packages.ID = " . intval($id);
	$results = db_query($q, $dbh);

	if (!$results) {
		print "<p>" . __("Error retrieving package details.") . "</p>\n";
	}
	else {
		$row = mysql_fetch_assoc($results);
		if (empty($row)) {
			print "<p>" . __("Package details could not be found.") . "</p>\n";

		}
		else {
			include('pkg_details.php');

			# Actions Bar
			if ($SID) {
				include('actions_form.php');
				include('pkg_comment_form.php');
			}

			# Print Comments
			$comments = package_comments($id, $dbh);
			if (!empty($comments)) {
				include('pkg_comments.php');
			}
		}
	}
	return;
}


/* pkg_search_page(SID)
 * outputs the body of search/search results page
 *
 * parameters:
 *  SID - current Session ID
 * preconditions:
 *  package search page has been accessed
 *  request variables have not been sanitized
 *
 *  request vars:
 *    O  - starting result number
 *    PP - number of search hits per page
 *    C  - package category ID number
 *    K  - package search string
 *    SO - search hit sort order:
 *          values: a - ascending
 *                  d - descending
 *    SB - sort search hits by:
 *          values: c - package category
 *                  n - package name
 *                  v - number of votes
 *                  m - maintainer username
 *    SeB- property that search string (K) represents
 *          values: n  - package name
 *                  nd - package name & description
 *                  x  - package name (exact match)
 *                  m  - package maintainer's username
 *                  s  - package submitter's username
 *    do_Orphans    - boolean. whether to search packages
 *                     without a maintainer
 *
 *
 *    These two are actually handled in packages.php.
 *
 *    IDs- integer array of ticked packages' IDs
 *    action - action to be taken on ticked packages
 *             values: do_Flag   - Flag out-of-date
 *                     do_UnFlag - Remove out-of-date flag
 *                     do_Adopt  - Adopt
 *                     do_Disown - Disown
 *                     do_Delete - Delete (requires confirm_Delete to be set)
 *                     do_Notify - Enable notification
 *                     do_UnNotify - Disable notification
 */
function pkg_search_page($SID="", $dbh=NULL) {
	if(!$dbh) {
		$dbh = db_connect();
	}

	// get commonly used variables...
	// TODO: REDUCE DB HITS.
	// grab info for user if they're logged in
	if ($SID)
		$myuid = uid_from_sid($SID, $dbh);
	// get a list of package categories
	$cats = pkgCategories($dbh); //meow

	// sanitize paging variables
	//
	if (isset($_GET['O'])) {
		$_GET['O'] = intval($_GET['O']);
		if ($_GET['O'] < 0)
			$_GET['O'] = 0;
	}
	else {
		$_GET['O'] = 0;
	}

	if (isset($_GET["PP"])) {
		$_GET["PP"] = intval($_GET["PP"]);
		if ($_GET["PP"] < 50)
			$_GET["PP"] = 50;
		else if ($_GET["PP"] > 250)
			$_GET["PP"] = 250;
	}
	else {
		$_GET["PP"] = 50;
	}

	// FIXME: pull out DB-related code. all of it.
	//        this one's worth a choco-chip cookie,
	//        one of those nice big soft ones

	// build the package search query
	//
	$q_select = "SELECT ";
	if ($SID) {
		$q_select .= "CommentNotify.UserID AS Notify,
			   PackageVotes.UsersID AS Voted, ";
	}
	$q_select .= "Users.Username AS Maintainer,
	PackageCategories.Category,
	Packages.Name, Packages.Version, Packages.Description, Packages.NumVotes,
	Packages.ID, Packages.OutOfDateTS ";

	$q_from = "FROM Packages
	LEFT JOIN Users ON (Packages.MaintainerUID = Users.ID)
	LEFT JOIN PackageCategories
	ON (Packages.CategoryID = PackageCategories.ID) ";
	if ($SID) {
		# this portion is not needed for the total row count query
		$q_from_extra = "LEFT JOIN PackageVotes
		ON (Packages.ID = PackageVotes.PackageID AND PackageVotes.UsersID = $myuid)
		LEFT JOIN CommentNotify
		ON (Packages.ID = CommentNotify.PkgID AND CommentNotify.UserID = $myuid) ";
	} else {
		$q_from_extra = "";
	}

	$q_where = "WHERE 1 = 1 ";
	// TODO: possibly do string matching on category
	//       to make request variable values more sensible
	if (isset($_GET["C"]) && intval($_GET["C"])) {
		$q_where .= "AND Packages.CategoryID = ".intval($_GET["C"])." ";
	}

	if (isset($_GET['K'])) {
		# Search by maintainer
		if (isset($_GET["SeB"]) && $_GET["SeB"] == "m") {
			$q_where .= "AND Users.Username = '".db_escape_string($_GET['K'])."' ";
		}
		# Search by submitter
		elseif (isset($_GET["SeB"]) && $_GET["SeB"] == "s") {
			$q_where .= "AND SubmitterUID = ".uid_from_username($_GET['K'], $dbh)." ";
		}
		# Search by name
		elseif (isset($_GET["SeB"]) && $_GET["SeB"] == "n") {
			$q_where .= "AND (Name LIKE '%".db_escape_like($_GET['K'])."%') ";
		}
		# Search by name (exact match)
		elseif (isset($_GET["SeB"]) && $_GET["SeB"] == "x") {
			$q_where .= "AND (Name = '".db_escape_string($_GET['K'])."') ";
		}
		# Search by name and description (Default)
		else {
			$q_where .= "AND (Name LIKE '%".db_escape_like($_GET['K'])."%' OR ";
			$q_where .= "Description LIKE '%".db_escape_like($_GET['K'])."%') ";
		}
	}

	if (isset($_GET["do_Orphans"])) {
		$q_where .= "AND MaintainerUID IS NULL ";
	}

	if (isset($_GET['outdated'])) {
		if ($_GET['outdated'] == 'on') {
			$q_where .= "AND OutOfDateTS IS NOT NULL ";
		}
		elseif ($_GET['outdated'] == 'off') {
			$q_where .= "AND OutOfDateTS IS NULL ";
		}
	}

	$order = (isset($_GET["SO"]) && $_GET["SO"] == 'd') ? 'DESC' : 'ASC';

	$q_sort = "ORDER BY Name ".$order." ";
	$sort_by = isset($_GET["SB"]) ? $_GET["SB"] : '';
	switch ($sort_by) {
	case 'c':
		$q_sort = "ORDER BY CategoryID ".$order.", Name ASC ";
		break;
	case 'v':
		$q_sort = "ORDER BY NumVotes ".$order.", Name ASC ";
		break;
	case 'w':
		if ($SID) {
			$q_sort = "ORDER BY Voted ".$order.", Name ASC ";
		}
		break;
	case 'o':
		if ($SID) {
			$q_sort = "ORDER BY Notify ".$order.", Name ASC ";
		}
		break;
	case 'm':
		$q_sort = "ORDER BY Maintainer ".$order.", Name ASC ";
		break;
	case 'a':
		$q_sort = "ORDER BY ModifiedTS ".$order.", Name ASC ";
		break;
	default:
		break;
	}

	$q_limit = "LIMIT ".$_GET["PP"]." OFFSET ".$_GET["O"];

	$q = $q_select . $q_from . $q_from_extra . $q_where . $q_sort . $q_limit;
	$q_total = "SELECT COUNT(*) " . $q_from . $q_where;

	$result = db_query($q, $dbh);
	$result_t = db_query($q_total, $dbh);
	if ($result_t) {
		$total = mysql_result($result_t, 0);
	}
	else {
		$total = 0;
	}

	if ($result && $total > 0) {
		if (isset($_GET["SO"]) && $_GET["SO"] == "d"){
			$SO_next = "a";
		}
		else {
			$SO_next = "d";
		}
	}

	// figure out the results to use
	$first = $_GET['O'] + 1;

	if (($_GET['PP'] + $_GET['O']) > $total) {
		$last = $total;
	} else {
		$last = $_GET['PP'] + $_GET['O'];
	}

	# calculation of pagination links
	$per_page = ($_GET['PP'] > 0) ? $_GET['PP'] : 50;
	$current = ceil($first / $per_page);
	$pages = ceil($total / $per_page);
	$templ_pages = array();

	if ($current > 1) {
		$templ_pages['&laquo; ' . __('First')] = 0;
		$templ_pages['&lsaquo; ' . __('Previous')] = ($current - 2) * $per_page;
	}

	if ($current - 5 > 1)
		$templ_pages["..."] = false;

	for ($i = max($current - 5, 1); $i <= min($pages, $current + 5); $i++) {
		$templ_pages[$i] = ($i - 1) * $per_page;
	}

	if ($current + 5 < $pages)
		$templ_pages["... "] = false;

	if ($current < $pages) {
		$templ_pages[__('Next') . ' &rsaquo;'] = $current * $per_page;
		$templ_pages[__('Last') . ' &raquo;'] = ($pages - 1) * $per_page;
	}

	include('pkg_search_form.php');
	include('pkg_search_results.php');

	return;
}

function current_action($action) {
	return (isset($_POST['action']) && $_POST['action'] == $action) ||
		isset($_POST[$action]);
}

/**
 * Ensure an array of IDs is in fact all valid integers.
 */
function sanitize_ids($ids) {
	$new_ids = array();
	foreach ($ids as $id) {
		$id = intval($id);
		if ($id > 0) {
			$new_ids[] = $id;
		}
	}
	return $new_ids;
}

/**
 * Flag and un-flag packages out-of-date
 *
 * @param string $atype Account type, output of account_from_sid
 * @param array $ids Array of package IDs to flag/unflag
 * @param boolean $action true flags out-of-date, false un-flags. Flags by
 * default
 *
 * @return string Translated success or error messages
 */
function pkg_flag ($atype, $ids, $action=true, $dbh=NULL) {
	global $AUR_LOCATION;

	if (!$atype) {
		if ($action) {
			return __("You must be logged in before you can flag packages.");
		} else {
			return __("You must be logged in before you can unflag packages.");
		}
	}

	$ids = sanitize_ids($ids);
	if (empty($ids)) {
		if ($action) {
			return __("You did not select any packages to flag.");
		} else {
			return __("You did not select any packages to unflag.");
		}
	}

	if(!$dbh) {
		$dbh = db_connect();
	}

	$q = "UPDATE Packages SET";
	if ($action) {
		$q.= " OutOfDateTS = UNIX_TIMESTAMP()";
	}
	else {
		$q.= " OutOfDateTS = NULL";
	}
	$q.= " WHERE ID IN (" . implode(",", $ids) . ")";

	db_query($q, $dbh);

	if ($action) {
		# Notify of flagging by email
		$f_name = username_from_sid($_COOKIE['AURSID'], $dbh);
		$f_email = email_from_sid($_COOKIE['AURSID'], $dbh);
		$f_uid = uid_from_sid($_COOKIE['AURSID'], $dbh);
		$q = "SELECT Packages.Name, Users.Email, Packages.ID ";
		$q.= "FROM Packages, Users ";
		$q.= "WHERE Packages.ID IN (" . implode(",", $ids) .") ";
		$q.= "AND Users.ID = Packages.MaintainerUID ";
		$q.= "AND Users.ID != " . $f_uid;
		$result = db_query($q, $dbh);
		if (mysql_num_rows($result)) {
			while ($row = mysql_fetch_assoc($result)) {
				# construct email
				$body = "Your package " . $row['Name'] . " has been flagged out of date by " . $f_name . " [1]. You may view your package at:\n" . $AUR_LOCATION . "/packages.php?ID=" . $row['ID'] . "\n\n[1] - " . $AUR_LOCATION . "/account.php?Action=AccountInfo&ID=" . $f_uid;
				$body = wordwrap($body, 70);
				$headers = "Reply-to: nobody@archlinux.org\nFrom:aur-notify@archlinux.org\nX-Mailer: PHP\nX-MimeOLE: Produced By AUR\n";
				@mail($row['Email'], "AUR Out-of-date Notification for ".$row['Name'], $body, $headers);
			}
		}
	}

	if ($action) {
		return __("The selected packages have been flagged out-of-date.");
	} else {
		return __("The selected packages have been unflagged.");
	}
}

/**
 * Delete packages
 *
 * @param string $atype Account type, output of account_from_sid
 * @param array $ids Array of package IDs to delete
 * @param int $mergepkgid Package to merge the deleted ones into
 *
 * @return string Translated error or success message
 */
function pkg_delete ($atype, $ids, $mergepkgid, $dbh=NULL) {
	if (!$atype) {
		return __("You must be logged in before you can delete packages.");
	}

	# If they're a TU or dev, can delete
	if ($atype != "Trusted User" && $atype != "Developer") {
		return __("You do have permission to delete packages.");
	}

	$ids = sanitize_ids($ids);
	if (empty($ids)) {
		return __("You did not select any packages to delete.");
	}

	if(!$dbh) {
		$dbh = db_connect();
	}

	if ($mergepkgid) {
		$mergepkgname = pkgname_from_id($mergepkgid, $dbh);
	}

	# Send email notifications
	foreach ($ids as $pkgid) {
		$q = 'SELECT CommentNotify.*, Users.Email ';
		$q.= 'FROM CommentNotify, Users ';
		$q.= 'WHERE Users.ID = CommentNotify.UserID ';
		$q.= 'AND CommentNotify.UserID != ' . uid_from_sid($_COOKIE['AURSID']) . ' ';
		$q.= 'AND CommentNotify.PkgID = ' . $pkgid;
		$result = db_query($q, $dbh);
		$bcc = array();

		while ($row = mysql_fetch_assoc($result)) {
			array_push($bcc, $row['Email']);
		}
		if (!empty($bcc)) {
			$pkgname = pkgname_from_id($pkgid);

			# TODO: native language emails for users, based on their prefs
			# Simply making these strings translatable won't work, users would be
			# getting emails in the language that the user who posted the comment was in
			$body = "";
			if ($mergepkgid) {
				$body .= username_from_sid($_COOKIE['AURSID']) . " merged \"".$pkgname."\" into \"$mergepkgname\".\n\n";
				$body .= "You will no longer receive notifications about this package, please go to https://aur.archlinux.org/packages.php?ID=".$mergepkgid." and click the Notify button if you wish to recieve them again.";
			} else {
				$body .= username_from_sid($_COOKIE['AURSID']) . " deleted \"".$pkgname."\".\n\n";
				$body .= "You will no longer receive notifications about this package.";
			}
			$body = wordwrap($body, 70);
			$bcc = implode(', ', $bcc);
			$headers = "Bcc: $bcc\nReply-to: nobody@archlinux.org\nFrom: aur-notify@archlinux.org\nX-Mailer: AUR\n";
			@mail('undisclosed-recipients: ;', "AUR Package deleted: " . $pkgname, $body, $headers);
		}
	}

	if ($mergepkgid) {
		/* Merge comments */
		$q = "UPDATE PackageComments ";
		$q.= "SET PackageID = " . intval($mergepkgid) . " ";
		$q.= "WHERE PackageID IN (" . implode(",", $ids) . ")";
		db_query($q, $dbh);

		/* Merge votes */
		foreach ($ids as $pkgid) {
			$q = "UPDATE PackageVotes ";
			$q.= "SET PackageID = " . intval($mergepkgid) . " ";
			$q.= "WHERE PackageID = " . $pkgid . " ";
			$q.= "AND UsersID NOT IN (";
			$q.= "SELECT * FROM (SELECT UsersID ";
			$q.= "FROM PackageVotes ";
			$q.= "WHERE PackageID = " . intval($mergepkgid);
			$q.= ") temp)";
			db_query($q, $dbh);
		}

		$q = "UPDATE Packages ";
		$q.= "SET NumVotes = (SELECT COUNT(*) FROM PackageVotes ";
		$q.= "WHERE PackageID = " . intval($mergepkgid) . ") ";
		$q.= "WHERE ID = " . intval($mergepkgid);
		db_query($q, $dbh);
	}

	$q = "DELETE FROM Packages WHERE ID IN (" . implode(",", $ids) . ")";
	$result = db_query($q, $dbh);

	return __("The selected packages have been deleted.");
}

/**
 * Adopt or disown packages
 *
 * @param string $atype Account type, output of account_from_sid
 * @param array $ids Array of package IDs to adopt/disown
 * @param boolean $action Adopts if true, disowns if false. Adopts by default
 *
 * @return string Translated error or success message
 */
function pkg_adopt ($atype, $ids, $action=true, $dbh=NULL) {
	if (!$atype) {
		if ($action) {
			return __("You must be logged in before you can adopt packages.");
		} else {
			return __("You must be logged in before you can disown packages.");
		}
	}

	$ids = sanitize_ids($ids);
	if (empty($ids)) {
		if ($action) {
			return __("You did not select any packages to adopt.");
		} else {
			return __("You did not select any packages to disown.");
		}
	}

	if(!$dbh) {
		$dbh = db_connect();
	}

	$field = "MaintainerUID";
	$q = "UPDATE Packages ";

	if ($action) {
		$user = uid_from_sid($_COOKIE["AURSID"], $dbh);
	} else {
		$user = 'NULL';
	}

	$q.= "SET $field = $user ";
	$q.= "WHERE ID IN (" . implode(",", $ids) . ") ";

	if ($action && $atype == "User") {
		# Regular users may only adopt orphan packages from unsupported
		$q.= "AND $field IS NULL ";
	} else if ($atype == "User") {
		$q.= "AND $field = " . uid_from_sid($_COOKIE["AURSID"], $dbh);
	}

	db_query($q, $dbh);

	if ($action) {
		pkg_notify(account_from_sid($_COOKIE["AURSID"], $dbh), $ids, $dbh);
		return __("The selected packages have been adopted.");
	} else {
		return __("The selected packages have been disowned.");
	}
}

/**
 * Vote and un-vote for packages
 *
 * @param string $atype Account type, output of account_from_sid
 * @param array $ids Array of package IDs to vote/un-vote
 * @param boolean $action Votes if true, un-votes if false. Votes by default
 *
 * @return string Translated error or success message
 */
function pkg_vote ($atype, $ids, $action=true, $dbh=NULL) {
	if (!$atype) {
		if ($action) {
			return __("You must be logged in before you can vote for packages.");
		} else {
			return __("You must be logged in before you can un-vote for packages.");
		}
	}

	$ids = sanitize_ids($ids);
	if (empty($ids)) {
		if ($action) {
			return __("You did not select any packages to vote for.");
		} else {
			return __("Your votes have been removed from the selected packages.");
		}
	}

	if(!$dbh) {
		$dbh = db_connect();
	}
	$my_votes = pkgvotes_from_sid($_COOKIE["AURSID"], $dbh);
	$uid = uid_from_sid($_COOKIE["AURSID"], $dbh);

	$first = 1;
	foreach ($ids as $pid) {
		if ($action) {
			$check = !isset($my_votes[$pid]);
		} else {
			$check = isset($my_votes[$pid]);
		}

		if ($check) {
			if ($first) {
				$first = 0;
				$vote_ids = $pid;
				if ($action) {
					$vote_clauses = "($uid, $pid)";
				}
			} else {
				$vote_ids .= ", $pid";
				if ($action) {
					$vote_clauses .= ", ($uid, $pid)";
				}
			}
		}
	}

	# only vote for packages the user hasn't already voted for
	#
	$op = $action ? "+" : "-";
	$q = "UPDATE Packages SET NumVotes = NumVotes $op 1 ";
	$q.= "WHERE ID IN ($vote_ids)";

	db_query($q, $dbh);

	if ($action) {
		$q = "INSERT INTO PackageVotes (UsersID, PackageID) VALUES ";
		$q.= $vote_clauses;
	} else {
		$q = "DELETE FROM PackageVotes WHERE UsersID = $uid ";
		$q.= "AND PackageID IN ($vote_ids)";
	}

	db_query($q, $dbh);

	if ($action) {
		$q = "UPDATE Users SET LastVoted = UNIX_TIMESTAMP() ";
		$q.= "WHERE ID = $uid";

		db_query($q, $dbh);
	}

	if ($action) {
		return __("Your votes have been cast for the selected packages.");
	} else {
		return __("Your votes have been removed from the selected packages.");
	}
}

# Get all usernames and ids for a specifc package id
function getvotes($pkgid, $dbh=NULL) {
	if(!$dbh) {
		$dbh = db_connect();
	}

	$pkgid = db_escape_string($pkgid);

	$q = "SELECT UsersID,Username FROM PackageVotes ";
	$q.= "LEFT JOIN Users on (UsersID = ID) ";
	$q.= "WHERE PackageID = ". $pkgid . " ";
	$q.= "ORDER BY Username";
	$result = db_query($q, $dbh);

	if (!$result) {
		return;
	}

	while ($row = mysql_fetch_assoc($result)) {
		$votes[] = $row;
	}

	return $votes;
}

/**
 * Toggle notification of packages
 *
 * @param string $atype Account type, output of account_from_sid
 * @param array $ids Array of package IDs to toggle, formatted as $package_id
 * @return string Translated error or success message
 */
function pkg_notify ($atype, $ids, $action=true, $dbh=NULL) {
	if (!$atype) {
#		return __("You must be logged in before you can get notifications on comments.");
		return;
	}

	$ids = sanitize_ids($ids);
	if (empty($ids)) {
		return __("Couldn't add to notification list.");
	}

	if(!$dbh) {
		$dbh = db_connect();
	}
	$uid = uid_from_sid($_COOKIE["AURSID"], $dbh);

	$output = "";

	$first = true;

	# There currently shouldn't be multiple requests here, but the
	# format in which it's sent requires this.
	foreach ($ids as $pid) {
		$q = "SELECT Name FROM Packages WHERE ID = $pid";
		$result = db_query($q, $dbh);
		if ($result) {
			$pkgname = mysql_result($result , 0);
		}
		else {
			$pkgname = '';
		}

		if ($first)
			$first = False;
		else
			$output .= ", ";


		if ($action) {
			$q = "SELECT * FROM CommentNotify WHERE UserID = $uid";
			$q .= " AND PkgID = $pid";

			# Notification already added. Don't add again.
			$result = db_query($q, $dbh);
			if (!mysql_num_rows($result)) {
				$q = "INSERT INTO CommentNotify (PkgID, UserID) VALUES ($pid, $uid)";
				db_query($q, $dbh);
			}

			$output .= $pkgname;
		}
		else {
			$q = "DELETE FROM CommentNotify WHERE PkgID = $pid";
			$q .= " AND UserID = $uid";
			db_query($q, $dbh);

			$output .= $pkgname;
		}
	}

	if ($action) {
		$output = __("You have been added to the comment notification list for %s.", $output);
	}
	else {
		$output = __("You have been removed from the comment notification list for %s.", $output);
	}

	return $output;
}



/**
 * Delete comment
 *
 * @param string $atype Account type, output of account_from_sid
 * @return string Translated error or success message
 */
function pkg_delete_comment($atype, $dbh=NULL) {
	if (!$atype) {
		return __("You must be logged in before you can edit package information.");
	}

	# Get ID of comment to be removed
	if (isset($_POST["comment_id"])) {
		$comment_id = $_POST["comment_id"];
	} else {
		return __("Missing comment ID.");
	}

	if(!$dbh) {
		$dbh = db_connect();
	}
	$uid = uid_from_sid($_COOKIE["AURSID"], $dbh);
	if (canDeleteComment($comment_id, $atype, $uid, $dbh)) {
		   $q = "UPDATE PackageComments ";
		   $q.= "SET DelUsersID = ".$uid." ";
		   $q.= "WHERE ID = ".intval($comment_id);
		   db_query($q, $dbh);
		   return __("Comment has been deleted.");
	} else {
		   return __("You are not allowed to delete this comment.");
	}
}

/**
 * Change package category
 *
 * @param string $atype Account type, output of account_from_sid
 * @return string Translated error or success message
 */
function pkg_change_category($atype, $dbh=NULL) {
	if (!$atype)  {
		return __("You must be logged in before you can edit package information.");
	}

	# Get ID of the new category
	if (isset($_POST["category_id"])) {
		$category_id = $_POST["category_id"];
	} else {
		return __("Missing category ID.");
	}

	if(!$dbh) {
		$dbh = db_connect();
	}
	$catArray = pkgCategories($dbh);
	if (!array_key_exists($category_id, $catArray)) {
		return __("Invalid category ID.");
	}

	if (isset($_GET["ID"])) {
		$pid = $_GET["ID"];
	} else {
		return __("Missing package ID.");
	}

	# Verify package ownership
	$q = "SELECT Packages.MaintainerUID ";
	$q.= "FROM Packages ";
	$q.= "WHERE Packages.ID = ".$pid;
	$result = db_query($q, $dbh);
	if ($result) {
		$pkg = mysql_fetch_assoc($result);
	}
	else {
		return __("You are not allowed to change this package category.");
	}

	$uid = uid_from_sid($_COOKIE["AURSID"], $dbh);
	if ($uid == $pkg["MaintainerUID"] ||
	($atype == "Developer" || $atype == "Trusted User")) {
		$q = "UPDATE Packages ";
		$q.= "SET CategoryID = ".intval($category_id)." ";
		$q.= "WHERE ID = ".intval($pid);
		db_query($q, $dbh);
		return __("Package category changed.");
	} else {
		return __("You are not allowed to change this package category.");
	}
}
