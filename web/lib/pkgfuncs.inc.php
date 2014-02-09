<?php
include_once("config.inc.php");

/**
 * Determine if the user can delete a specific package comment
 *
 * Only the comment submitter, Trusted Users, and Developers can delete
 * comments. This function is used for the backend side of comment deletion.
 *
 * @param string $comment_id The comment ID in the database
 * @param string $atype The account type of the user trying to delete a comment
 * @param string|int $uid The user ID of the individual trying to delete a comment
 *
 * @return bool True if the user can delete the comment, otherwise false
 */
function canDeleteComment($comment_id=0, $atype="", $uid=0) {
	if (!$uid) {
		/* Unauthenticated users cannot delete anything. */
		return false;
	}
	if ($atype == "Trusted User" || $atype == "Developer") {
		/* TUs and developers can delete any comment. */
		return true;
	}

	$dbh = DB::connect();

	$q = "SELECT COUNT(*) FROM PackageComments ";
	$q.= "WHERE ID = " . intval($comment_id) . " AND UsersID = " . $uid;
	$result = $dbh->query($q);

	if (!$result) {
		return false;
	}

	$row = $result->fetch(PDO::FETCH_NUM);
	return ($row[0] > 0);
}

/**
 * Determine if the user can delete a specific package comment using an array
 *
 * Only the comment submitter, Trusted Users, and Developers can delete
 * comments. This function is used for the frontend side of comment deletion.
 *
 * @param array $comment All database information relating a specific comment
 * @param string $atype The account type of the user trying to delete a comment
 * @param string|int $uid The user ID of the individual trying to delete a comment
 *
 * @return bool True if the user can delete the comment, otherwise false
 */
function canDeleteCommentArray($comment, $atype="", $uid=0) {
	if (!$uid) {
		/* Unauthenticated users cannot delete anything. */
		return false;
	} elseif ($atype == "Trusted User" || $atype == "Developer") {
		/* TUs and developers can delete any comment. */
		return true;
	} else if ($comment['UsersID'] == $uid) {
		/* Users can delete their own comments. */
		return true;
	}
	return false;
}

/**
 * Determine if the visitor can submit blacklisted packages.
 *
 * Only Trusted Users and Developers can delete blacklisted packages. Packages
 * are blacklisted if they are include in the official repositories.
 *
 * @param string $atype The account type of the user
 *
 * @return bool True if the user can submit blacklisted packages, otherwise false
 */
function canSubmitBlacklisted($atype = "") {
	if ($atype == "Trusted User" || $atype == "Developer") {
		/* Only TUs and developers can submit blacklisted packages. */
		return true;
	}
	else {
		return false;
	}
}

/**
 * Get all package categories stored in the database
 *
 * @param \PDO An already established database connection
 *
 * @return array All package categories
 */
function pkgCategories() {
	$cats = array();
	$dbh = DB::connect();
	$q = "SELECT * FROM PackageCategories WHERE ID != 1 ";
	$q.= "ORDER BY Category ASC";
	$result = $dbh->query($q);
	if ($result) {
		while ($row = $result->fetch(PDO::FETCH_NUM)) {
			$cats[$row[0]] = $row[1];
		}
	}
	return $cats;
}

/**
 * Check to see if the package name already exists in the database
 *
 * @param string $name The package name to check
 *
 * @return string|void Package name if it already exists
 */
function pkgid_from_name($name="") {
	if (!$name) {return NULL;}
	$dbh = DB::connect();
	$q = "SELECT ID FROM Packages ";
	$q.= "WHERE Name = " . $dbh->quote($name);
	$result = $dbh->query($q);
	if (!$result) {
		return;
	}
	$row = $result->fetch(PDO::FETCH_NUM);
	return $row[0];
}

/**
 * Get package dependencies for a specific package
 *
 * @param int $pkgid The package to get dependencies for
 *
 * @return array All package dependencies for the package
 */
function package_dependencies($pkgid) {
	$deps = array();
	$pkgid = intval($pkgid);
	if ($pkgid > 0) {
		$dbh = DB::connect();
		$q = "SELECT pd.DepName, pd.DepCondition, p.ID FROM PackageDepends pd ";
		$q.= "LEFT JOIN Packages p ON pd.DepName = p.Name ";
		$q.= "WHERE pd.PackageID = ". $pkgid . " ";
		$q.= "ORDER BY pd.DepName";
		$result = $dbh->query($q);
		if (!$result) {
			return array();
		}
		while ($row = $result->fetch(PDO::FETCH_NUM)) {
			$deps[] = $row;
		}
	}
	return $deps;
}

/**
 * Determine packages that depend on a package
 *
 * @param string $name The package name for the dependency search
 *
 * @return array All packages that depend on the specified package name
 */
function package_required($name="") {
	$deps = array();
	if ($name != "") {
		$dbh = DB::connect();
		$q = "SELECT DISTINCT p.Name, PackageID FROM PackageDepends pd ";
		$q.= "JOIN Packages p ON pd.PackageID = p.ID ";
		$q.= "WHERE DepName = " . $dbh->quote($name) . " ";
		$q.= "ORDER BY p.Name";
		$result = $dbh->query($q);
		if (!$result) {return array();}
		while ($row = $result->fetch(PDO::FETCH_NUM)) {
			$deps[] = $row;
		}
	}
	return $deps;
}

/**
 * Get the number of non-deleted comments for a specific package
 *
 * @param string $pkgid The package ID to get comment count for
 *
 * @return string The number of comments left for a specific package
 */
function package_comments_count($pkgid) {
	$dbh = DB::connect();

	$pkgid = intval($pkgid);
	if ($pkgid > 0) {
		$dbh = DB::connect();
		$q = "SELECT COUNT(*) FROM PackageComments ";
		$q.= "WHERE PackageID = " . $pkgid;
		$q.= " AND DelUsersID IS NULL";
	}
	$result = $dbh->query($q);

	if (!$result) {
		return;
	}

	$row = $result->fetch(PDO::FETCH_NUM);
	return $row[0];
}

/**
 * Get all package comment information for a specific package
 *
 * @param int $pkgid The package ID to get comments for
 *
 * @return array All package comment information for a specific package
 */
function package_comments($pkgid) {
	$comments = array();
	$pkgid = intval($pkgid);
	if ($pkgid > 0) {
		$dbh = DB::connect();
		$q = "SELECT PackageComments.ID, UserName, UsersID, Comments, CommentTS ";
		$q.= "FROM PackageComments LEFT JOIN Users ";
		$q.= "ON PackageComments.UsersID = Users.ID ";
		$q.= "WHERE PackageID = " . $pkgid . " ";
		$q.= "AND DelUsersID IS NULL ";
		$q.= "ORDER BY CommentTS DESC";

		if (!isset($_GET['comments'])) {
			$q.= " LIMIT 10";
		}

		$result = $dbh->query($q);

		if (!$result) {
			return;
		}

		while ($row = $result->fetch(PDO::FETCH_ASSOC)) {
			$comments[] = $row;
		}
	}
	return $comments;
}

/**
 * Add a comment to a package page and send out appropriate notifications
 *
 * @global string $AUR_LOCATION The AUR's URL used for notification e-mails
 * @param string $pkgid The package ID to add the comment on
 * @param string $uid The user ID of the individual who left the comment
 * @param string $comment The comment left on a package page
 *
 * @return void
 */
function add_package_comment($pkgid, $uid, $comment) {
	global $AUR_LOCATION;

	$dbh = DB::connect();

	$q = "INSERT INTO PackageComments ";
	$q.= "(PackageID, UsersID, Comments, CommentTS) VALUES (";
	$q.= intval($pkgid) . ", " . $uid . ", ";
	$q.= $dbh->quote($comment) . ", UNIX_TIMESTAMP())";
	$dbh->exec($q);

	/*
	 * Send e-mail notifications.
	 * TODO: Move notification logic to separate function where it belongs.
	 */
	$q = "SELECT CommentNotify.*, Users.Email ";
	$q.= "FROM CommentNotify, Users ";
	$q.= "WHERE Users.ID = CommentNotify.UserID ";
	$q.= "AND CommentNotify.UserID != " . $uid . " ";
	$q.= "AND CommentNotify.PkgID = " . intval($pkgid);
	$result = $dbh->query($q);
	$bcc = array();

	if ($result) {
		while ($row = $result->fetch(PDO::FETCH_ASSOC)) {
			array_push($bcc, $row['Email']);
		}

		$q = "SELECT Packages.* ";
		$q.= "FROM Packages ";
		$q.= "WHERE Packages.ID = " . intval($pkgid);
		$result = $dbh->query($q);
		$row = $result->fetch(PDO::FETCH_ASSOC);

		/*
		 * TODO: Add native language emails for users, based on their
		 * preferences. Simply making these strings translatable won't
		 * work, users would be getting emails in the language that the
		 * user who posted the comment was in.
		 */
		$body =
		'from ' . $AUR_LOCATION . get_pkg_uri($row['Name']) . "\n"
		. username_from_sid($_COOKIE['AURSID']) . " wrote:\n\n"
		. $comment
		. "\n\n---\nIf you no longer wish to receive notifications about this package, please go the the above package page and click the UnNotify button.";
		$body = wordwrap($body, 70);
		$bcc = implode(', ', $bcc);
		$headers = "Bcc: $bcc\nReply-to: nobody@archlinux.org\nFrom: aur-notify@archlinux.org\nX-Mailer: AUR\n";
		@mail('undisclosed-recipients: ;', "AUR Comment for " . $row['Name'], $body, $headers);
	}
}

/**
 * Get all package sources for a specific package
 *
 * @param string $pkgid The package ID to get the sources for
 *
 * @return array All sources associated with a specific package
 */
function package_sources($pkgid) {
	$sources = array();
	$pkgid = intval($pkgid);
	if ($pkgid > 0) {
		$dbh = DB::connect();
		$q = "SELECT Source FROM PackageSources ";
		$q.= "WHERE PackageID = " . $pkgid;
		$q.= " ORDER BY Source";
		$result = $dbh->query($q);
		if (!$result) {
			return array();
		}
		while ($row = $result->fetch(PDO::FETCH_NUM)) {
			$sources[] = $row[0];
		}
	}
	return $sources;
}

/**
 * Get a list of all packages a logged-in user has voted for
 *
 * @param string $sid The session ID of the visitor
 *
 * @return array All packages the visitor has voted for
 */
function pkgvotes_from_sid($sid="") {
	$pkgs = array();
	if (!$sid) {return $pkgs;}
	$dbh = DB::connect();
	$q = "SELECT PackageID ";
	$q.= "FROM PackageVotes, Users, Sessions ";
	$q.= "WHERE Users.ID = Sessions.UsersID ";
	$q.= "AND Users.ID = PackageVotes.UsersID ";
	$q.= "AND Sessions.SessionID = " . $dbh->quote($sid);
	$result = $dbh->query($q);
	if ($result) {
		while ($row = $result->fetch(PDO::FETCH_NUM)) {
			$pkgs[$row[0]] = 1;
		}
	}
	return $pkgs;
}

/**
 * Determine package names from package IDs
 *
 * @param string|array $pkgids The package IDs to get names for
 *
 * @return array|string All names if multiple package IDs, otherwise package name
 */
function pkgname_from_id($pkgids) {
	if (is_array($pkgids)) {
		$pkgids = sanitize_ids($pkgids);
		$names = array();
		$dbh = DB::connect();
		$q = "SELECT Name FROM Packages WHERE ID IN (";
		$q.= implode(",", $pkgids) . ")";
		$result = $dbh->query($q);
		if ($result) {
			while ($row = $result->fetch(PDO::FETCH_ASSOC)) {
				$names[] = $row['Name'];
			}
		}
		return $names;
	}
	elseif ($pkgids > 0) {
		$dbh = DB::connect();
		$q = "SELECT Name FROM Packages WHERE ID = " . $pkgids;
		$result = $dbh->query($q);
		if ($result) {
			$name = $result->fetch(PDO::FETCH_NUM);
		}
		return $name[0];
	}
	else {
		return NULL;
	}
}

/**
 * Determine if a package name is on the database blacklist
 *
 * @param string $name The package name to check
 *
 * @return bool True if the name is blacklisted, otherwise false
 */
function pkgname_is_blacklisted($name) {
	$dbh = DB::connect();
	$q = "SELECT COUNT(*) FROM PackageBlacklist ";
	$q.= "WHERE Name = " . $dbh->quote($name);
	$result = $dbh->query($q);

	if (!$result) return false;
	return ($result->fetchColumn() > 0);
}

/**
 * Get the package details
 *
 * @param string $id The package ID to get description for
 *
 * @return array The package's details OR error message
 **/
function get_package_details($id=0) {
	$dbh = DB::connect();

	$q = "SELECT Packages.*,Category ";
	$q.= "FROM Packages,PackageCategories ";
	$q.= "WHERE Packages.CategoryID = PackageCategories.ID ";
	$q.= "AND Packages.ID = " . intval($id);
	$result = $dbh->query($q);

	$row = array();

	if (!$result) {
		$row['error'] = __("Error retrieving package details.");
	}
	else {
		$row = $result->fetch(PDO::FETCH_ASSOC);
		if (empty($row)) {
			$row['error'] = __("Package details could not be found.");
		}
	}

	return $row;
}

/**
 * Display the package details page
 *
 * @global string $AUR_LOCATION The AUR's URL used for notification e-mails
 * @global bool $USE_VIRTUAL_URLS True if using URL rewriting, otherwise false
 * @param string $id The package ID to get details page for
 * @param array $row Package details retrieved by get_package_details
 * @param string $SID The session ID of the visitor
 *
 * @return void
 */
function display_package_details($id=0, $row, $SID="") {
	global $AUR_LOCATION;
	global $USE_VIRTUAL_URLS;

	$dbh = DB::connect();

	if (isset($row['error'])) {
		print "<p>" . $row['error'] . "</p>\n";
	}
	else {
		include('pkg_details.php');

		if ($SID) {
			include('actions_form.php');
			include('pkg_comment_form.php');
		}

		$comments = package_comments($id);
		if (!empty($comments)) {
			include('pkg_comments.php');
		}
	}
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
function pkg_search_page($SID="") {
	$dbh = DB::connect();

	/*
	 * Get commonly used variables.
	 * TODO: Reduce the number of database queries!
	 */
	if ($SID)
		$myuid = uid_from_sid($SID);
	$cats = pkgCategories($dbh);

	/* Sanitize paging variables. */
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

	/*
	 * FIXME: Pull out DB-related code. All of it! This one's worth a
	 * choco-chip cookie, one of those nice big soft ones.
	 */

	/* Build the package search query. */
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
		/* This is not needed for the total row count query. */
		$q_from_extra = "LEFT JOIN PackageVotes
		ON (Packages.ID = PackageVotes.PackageID AND PackageVotes.UsersID = $myuid)
		LEFT JOIN CommentNotify
		ON (Packages.ID = CommentNotify.PkgID AND CommentNotify.UserID = $myuid) ";
	} else {
		$q_from_extra = "";
	}

	$q_where = "WHERE 1 = 1 ";
	/*
	 * TODO: Possibly do string matching on category to make request
	 * variable values more sensible.
	 */
	if (isset($_GET["C"]) && intval($_GET["C"])) {
		$q_where .= "AND Packages.CategoryID = ".intval($_GET["C"])." ";
	}

	if (isset($_GET['K'])) {
		if (isset($_GET["SeB"]) && $_GET["SeB"] == "m") {
			/* Search by maintainer. */
			$q_where .= "AND Users.Username = " . $dbh->quote($_GET['K']) . " ";
		}
		elseif (isset($_GET["SeB"]) && $_GET["SeB"] == "s") {
			/* Search by submitter. */
			$q_where .= "AND SubmitterUID = ".uid_from_username($_GET['K'])." ";
		}
		elseif (isset($_GET["SeB"]) && $_GET["SeB"] == "n") {
			/* Search by name. */
			$K = "%" . addcslashes($_GET['K'], '%_') . "%";
			$q_where .= "AND (Name LIKE " . $dbh->quote($K) . ") ";
		}
		elseif (isset($_GET["SeB"]) && $_GET["SeB"] == "x") {
			/* Search by name (exact match). */
			$q_where .= "AND (Name = " . $dbh->quote($_GET['K']) . ") ";
		}
		else {
			/* Search by name and description (default). */
			$K = "%" . addcslashes($_GET['K'], '%_') . "%";
			$q_where .= "AND (Name LIKE " . $dbh->quote($K) . " OR ";
			$q_where .= "Description LIKE " . $dbh->quote($K) . ") ";
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

	$result = $dbh->query($q);
	$result_t = $dbh->query($q_total);
	if ($result_t) {
		$row = $result_t->fetch(PDO::FETCH_NUM);
		$total = $row[0];
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

	/* Calculate the results to use. */
	$first = $_GET['O'] + 1;

	/* Calculation of pagination links. */
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

	if ($result) {
		while ($row = $result->fetch(PDO::FETCH_ASSOC)) {
			$searchresults[] = $row;
		}
	}

	include('pkg_search_results.php');

	return;
}

/**
 * Determine if a POST string has been sent by a visitor
 *
 * @param string $action String to check has been sent via POST
 *
 * @return bool True if the POST string was used, otherwise false
 */
function current_action($action) {
	return (isset($_POST['action']) && $_POST['action'] == $action) ||
		isset($_POST[$action]);
}

/**
 * Determine if sent IDs are valid integers
 *
 * @param array $ids IDs to validate
 *
 * @return array All sent IDs that are valid integers
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
 * Flag package(s) as out-of-date
 *
 * @global string $AUR_LOCATION The AUR's URL used for notification e-mails
 * @param string $atype Account type, output of account_from_sid
 * @param array $ids Array of package IDs to flag/unflag
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkg_flag($atype, $ids) {
	global $AUR_LOCATION;

	if (!$atype) {
		return array(false, __("You must be logged in before you can flag packages."));
	}

	$ids = sanitize_ids($ids);
	if (empty($ids)) {
		return array(false, __("You did not select any packages to flag."));
	}

	$dbh = DB::connect();

	$q = "UPDATE Packages SET";
	$q.= " OutOfDateTS = UNIX_TIMESTAMP()";
	$q.= " WHERE ID IN (" . implode(",", $ids) . ")";
	$q.= " AND OutOfDateTS IS NULL";

	$affected_pkgs = $dbh->exec($q);

	if ($affected_pkgs > 0) {
		/* Notify of flagging by e-mail. */
		$f_name = username_from_sid($_COOKIE['AURSID']);
		$f_email = email_from_sid($_COOKIE['AURSID']);
		$f_uid = uid_from_sid($_COOKIE['AURSID']);
		$q = "SELECT Packages.Name, Users.Email, Packages.ID ";
		$q.= "FROM Packages, Users ";
		$q.= "WHERE Packages.ID IN (" . implode(",", $ids) .") ";
		$q.= "AND Users.ID = Packages.MaintainerUID ";
		$q.= "AND Users.ID != " . $f_uid;
		$result = $dbh->query($q);
		if ($result) {
			while ($row = $result->fetch(PDO::FETCH_ASSOC)) {
				$body = "Your package " . $row['Name'] . " has been flagged out of date by " . $f_name . " [1]. You may view your package at:\n" . $AUR_LOCATION . get_pkg_uri($row['Name']) . "\n\n[1] - " . $AUR_LOCATION . get_user_uri($f_name);
				$body = wordwrap($body, 70);
				$headers = "Reply-to: nobody@archlinux.org\nFrom:aur-notify@archlinux.org\nX-Mailer: PHP\nX-MimeOLE: Produced By AUR\n";
				@mail($row['Email'], "AUR Out-of-date Notification for ".$row['Name'], $body, $headers);
			}
		}
	}

	return array(true, __("The selected packages have been flagged out-of-date."));
}

/**
 * Unflag package(s) as out-of-date
 *
 * @param string $atype Account type, output of account_from_sid
 * @param array $ids Array of package IDs to flag/unflag
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkg_unflag($atype, $ids) {
	if (!$atype) {
		return array(false, __("You must be logged in before you can unflag packages."));
	}

	$ids = sanitize_ids($ids);
	if (empty($ids)) {
		return array(false, __("You did not select any packages to unflag."));
	}

	$dbh = DB::connect();

	$q = "UPDATE Packages SET ";
	$q.= "OutOfDateTS = NULL ";
	$q.= "WHERE ID IN (" . implode(",", $ids) . ") ";

	if ($atype != "Trusted User" && $atype != "Developer") {
		$q.= "AND MaintainerUID = " . uid_from_sid($_COOKIE["AURSID"]);
	}

	$result = $dbh->exec($q);

	if ($result) {
		return array(true, __("The selected packages have been unflagged."));
	}
}

/**
 * Delete packages
 *
 * @param string $atype Account type, output of account_from_sid
 * @param array $ids Array of package IDs to delete
 * @param int $mergepkgid Package to merge the deleted ones into
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkg_delete ($atype, $ids, $mergepkgid) {
	if (!$atype) {
		return array(false, __("You must be logged in before you can delete packages."));
	}

	if ($atype != "Trusted User" && $atype != "Developer") {
		return array(false, __("You do not have permission to delete packages."));
	}

	$ids = sanitize_ids($ids);
	if (empty($ids)) {
		return array(false, __("You did not select any packages to delete."));
	}

	$dbh = DB::connect();

	if ($mergepkgid) {
		$mergepkgname = pkgname_from_id($mergepkgid);
	}

	/* Send e-mail notifications. */
	foreach ($ids as $pkgid) {
		$q = "SELECT CommentNotify.*, Users.Email ";
		$q.= "FROM CommentNotify, Users ";
		$q.= "WHERE Users.ID = CommentNotify.UserID ";
		$q.= "AND CommentNotify.UserID != " . uid_from_sid($_COOKIE['AURSID']) . " ";
		$q.= "AND CommentNotify.PkgID = " . $pkgid;
		$result = $dbh->query($q);
		$bcc = array();

		while ($row = $result->fetch(PDO::FETCH_ASSOC)) {
			array_push($bcc, $row['Email']);
		}
		if (!empty($bcc)) {
			$pkgname = pkgname_from_id($pkgid);

			/*
			 * TODO: Add native language emails for users, based on
			 * their preferences. Simply making these strings
			 * translatable won't work, users would be getting
			 * emails in the language that the user who posted the
			 * comment was in.
			 */
			$body = "";
			if ($mergepkgid) {
				$body .= username_from_sid($_COOKIE['AURSID']) . " merged \"".$pkgname."\" into \"$mergepkgname\".\n\n";
				$body .= "You will no longer receive notifications about this package, please go to https://aur.archlinux.org" . get_pkg_uri($mergepkgname) . " and click the Notify button if you wish to recieve them again.";
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
		$dbh->exec($q);

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
			$dbh->exec($q);
		}

		$q = "UPDATE Packages ";
		$q.= "SET NumVotes = (SELECT COUNT(*) FROM PackageVotes ";
		$q.= "WHERE PackageID = " . intval($mergepkgid) . ") ";
		$q.= "WHERE ID = " . intval($mergepkgid);
		$dbh->exec($q);
	}

	$q = "DELETE FROM Packages WHERE ID IN (" . implode(",", $ids) . ")";
	$result = $dbh->exec($q);

	return array(true, __("The selected packages have been deleted."));
}

/**
 * Adopt or disown packages
 *
 * @param string $atype Account type, output of account_from_sid
 * @param array $ids Array of package IDs to adopt/disown
 * @param bool $action Adopts if true, disowns if false. Adopts by default
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkg_adopt ($atype, $ids, $action=true) {
	if (!$atype) {
		if ($action) {
			return array(false, __("You must be logged in before you can adopt packages."));
		} else {
			return array(false, __("You must be logged in before you can disown packages."));
		}
	}

	$ids = sanitize_ids($ids);
	if (empty($ids)) {
		if ($action) {
			return array(false, __("You did not select any packages to adopt."));
		} else {
			return array(false, __("You did not select any packages to disown."));
		}
	}

	$dbh = DB::connect();

	$field = "MaintainerUID";
	$q = "UPDATE Packages ";

	if ($action) {
		$user = uid_from_sid($_COOKIE["AURSID"]);
	} else {
		$user = 'NULL';
	}

	$q.= "SET $field = $user ";
	$q.= "WHERE ID IN (" . implode(",", $ids) . ") ";

	if ($action && $atype == "User") {
		/* Regular users may only adopt orphan packages. */
		$q.= "AND $field IS NULL ";
	} else if ($atype == "User") {
		$q.= "AND $field = " . uid_from_sid($_COOKIE["AURSID"]);
	}

	$dbh->exec($q);

	if ($action) {
		pkg_notify(account_from_sid($_COOKIE["AURSID"]), $ids);
		return array(true, __("The selected packages have been adopted."));
	} else {
		return array(true, __("The selected packages have been disowned."));
	}
}

/**
 * Vote and un-vote for packages
 *
 * @param string $atype Account type, output of account_from_sid
 * @param array $ids Array of package IDs to vote/un-vote
 * @param bool $action Votes if true, un-votes if false. Votes by default
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkg_vote ($atype, $ids, $action=true) {
	if (!$atype) {
		if ($action) {
			return array(false, __("You must be logged in before you can vote for packages."));
		} else {
			return array(false, __("You must be logged in before you can un-vote for packages."));
		}
	}

	$ids = sanitize_ids($ids);
	if (empty($ids)) {
		if ($action) {
			return array(false, __("You did not select any packages to vote for."));
		} else {
			return array(false, __("Your votes have been removed from the selected packages."));
		}
	}

	$dbh = DB::connect();
	$my_votes = pkgvotes_from_sid($_COOKIE["AURSID"]);
	$uid = uid_from_sid($_COOKIE["AURSID"]);

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

	/* Only add votes for packages the user hasn't already voted for. */
	$op = $action ? "+" : "-";
	$q = "UPDATE Packages SET NumVotes = NumVotes $op 1 ";
	$q.= "WHERE ID IN ($vote_ids)";

	$dbh->exec($q);

	if ($action) {
		$q = "INSERT INTO PackageVotes (UsersID, PackageID) VALUES ";
		$q.= $vote_clauses;
	} else {
		$q = "DELETE FROM PackageVotes WHERE UsersID = $uid ";
		$q.= "AND PackageID IN ($vote_ids)";
	}

	$dbh->exec($q);

	if ($action) {
		return array(true, __("Your votes have been cast for the selected packages."));
	} else {
		return array(true, __("Your votes have been removed from the selected packages."));
	}
}

/**
 * Get all usernames and IDs that voted for a specific package
 *
 * @param string $pkgname The name of the package to retrieve votes for
 *
 * @return array User IDs and usernames that voted for a specific package
 */
function votes_for_pkgname($pkgname) {
	$dbh = DB::connect();

	$q = "SELECT UsersID,Username,Name FROM PackageVotes ";
	$q.= "LEFT JOIN Users on (UsersID = Users.ID) ";
	$q.= "LEFT JOIN Packages on (PackageID = Packages.ID) ";
	$q.= "WHERE Name = ". $dbh->quote($pkgname) . " ";
	$q.= "ORDER BY Username";
	$result = $dbh->query($q);

	if (!$result) {
		return;
	}

	$votes = array();
	while ($row = $result->fetch(PDO::FETCH_ASSOC)) {
		$votes[] = $row;
	}

	return $votes;
}

/**
 * Determine if a user has already voted for a specific package
 *
 * @param string $uid The user ID to check for an existing vote
 * @param string $pkgid The package ID to check for an existing vote
 *
 * @return bool True if the user has already voted, otherwise false
 */
function user_voted($uid, $pkgid) {
	$dbh = DB::connect();

	$q = "SELECT * FROM PackageVotes WHERE UsersID = ". $dbh->quote($uid);
	$q.= " AND PackageID = " . $dbh->quote($pkgid);
	$result = $dbh->query($q);

	if ($result->fetch(PDO::FETCH_NUM)) {
		return true;
	}
	else {
		return false;
	}
}

/**
 * Determine if a user wants notifications for a specific package
 *
 * @param string $uid User ID to check in the database
 * @param string $pkgid Package ID to check notifications for
 *
 * @return bool True if the user wants notifications, otherwise false
 */
function user_notify($uid, $pkgid) {
	$dbh = DB::connect();

	$q = "SELECT * FROM CommentNotify WHERE UserID = " . $dbh->quote($uid);
	$q.= " AND PkgID = " . $dbh->quote($pkgid);
	$result = $dbh->query($q);

	if ($result->fetch(PDO::FETCH_NUM)) {
		return true;
	}
	else {
		return false;
	}
}

/**
 * Toggle notification of packages
 *
 * @param string $atype Account type, output of account_from_sid
 * @param array $ids Array of package IDs to toggle, formatted as $package_id
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkg_notify ($atype, $ids, $action=true) {
	if (!$atype) {
		return;
	}

	$ids = sanitize_ids($ids);
	if (empty($ids)) {
		return array(false, __("Couldn't add to notification list."));
	}

	$dbh = DB::connect();
	$uid = uid_from_sid($_COOKIE["AURSID"]);

	$output = "";

	$first = true;

	/*
	 * There currently shouldn't be multiple requests here, but the format
	 * in which it's sent requires this.
	 */
	foreach ($ids as $pid) {
		$q = "SELECT Name FROM Packages WHERE ID = $pid";
		$result = $dbh->query($q);
		if ($result) {
			$row = $result->fetch(PDO::FETCH_NUM);
			$pkgname = $row[0];
		}
		else {
			$pkgname = '';
		}

		if ($first)
			$first = false;
		else
			$output .= ", ";


		if ($action) {
			$q = "SELECT COUNT(*) FROM CommentNotify WHERE ";
			$q .= "UserID = $uid AND PkgID = $pid";

			/* Notification already added. Don't add again. */
			$result = $dbh->query($q);
			if ($result->fetchColumn() == 0) {
				$q = "INSERT INTO CommentNotify (PkgID, UserID) VALUES ($pid, $uid)";
				$dbh->exec($q);
			}

			$output .= $pkgname;
		}
		else {
			$q = "DELETE FROM CommentNotify WHERE PkgID = $pid ";
			$q .= "AND UserID = $uid";
			$dbh->exec($q);

			$output .= $pkgname;
		}
	}

	if ($action) {
		$output = __("You have been added to the comment notification list for %s.", $output);
	}
	else {
		$output = __("You have been removed from the comment notification list for %s.", $output);
	}

	return array(true, $output);
}

/**
 * Delete a package comment
 *
 * @param string $atype Account type, output of account_from_sid
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkg_delete_comment($atype) {
	if (!$atype) {
		return array(false, __("You must be logged in before you can edit package information."));
	}

	if (isset($_POST["comment_id"])) {
		$comment_id = $_POST["comment_id"];
	} else {
		return array(false, __("Missing comment ID."));
	}

	$dbh = DB::connect();
	$uid = uid_from_sid($_COOKIE["AURSID"]);
	if (canDeleteComment($comment_id, $atype, $uid)) {
		   $q = "UPDATE PackageComments ";
		   $q.= "SET DelUsersID = ".$uid." ";
		   $q.= "WHERE ID = ".intval($comment_id);
		$dbh->exec($q);
		   return array(true, __("Comment has been deleted."));
	} else {
		   return array(false, __("You are not allowed to delete this comment."));
	}
}

/**
 * Change package category
 *
 * @param string $atype Account type, output of account_from_sid
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkg_change_category($pid, $atype) {
	if (!$atype)  {
		return array(false, __("You must be logged in before you can edit package information."));
	}

	if (isset($_POST["category_id"])) {
		$category_id = $_POST["category_id"];
	} else {
		return array(false, __("Missing category ID."));
	}

	$dbh = DB::connect();
	$catArray = pkgCategories($dbh);
	if (!array_key_exists($category_id, $catArray)) {
		return array(false, __("Invalid category ID."));
	}

	/* Verify package ownership. */
	$q = "SELECT Packages.MaintainerUID ";
	$q.= "FROM Packages ";
	$q.= "WHERE Packages.ID = ".$pid;
	$result = $dbh->query($q);
	if ($result) {
		$row = $result->fetch(PDO::FETCH_ASSOC);
	}
	else {
		return array(false, __("You are not allowed to change this package category."));
	}

	$uid = uid_from_sid($_COOKIE["AURSID"]);
	if ($uid == $row["MaintainerUID"] ||
	($atype == "Developer" || $atype == "Trusted User")) {
		$q = "UPDATE Packages ";
		$q.= "SET CategoryID = ".intval($category_id)." ";
		$q.= "WHERE ID = ".intval($pid);
		$dbh->exec($q);
		return array(true, __("Package category changed."));
	} else {
		return array(false, __("You are not allowed to change this package category."));
	}
}

/**
 * Get all package information in the database for a specific package
 *
 * @param string $pkgname The name of the package to get details for
 *
 * @return array All package details for a specific package
 */
function pkgdetails_by_pkgname($pkgname) {
	$dbh = DB::connect();
	$q = "SELECT * FROM Packages WHERE Name = " . $dbh->quote($pkgname);
	$result = $dbh->query($q);
	if ($result) {
		$row = $result->fetch(PDO::FETCH_ASSOC);
	}
	return $row;
}

/**
 * Add package information to the database for a specific package
 *
 * @param string $pkgname Name of the new package
 * @param string $license License of the new package
 * @param string $pkgver Version of the new package
 * @param int $category_id Category for the new package
 * @param string $pkgdesc Description of the new package
 * @param string $pkgurl Upstream URL for the new package
 * @param int $uid User ID of the package uploader
 *
 * @return void
 */
function new_pkgdetails($pkgname, $license, $pkgver, $category_id, $pkgdesc, $pkgurl, $uid) {
	$dbh = DB::connect();
	$q = sprintf("INSERT INTO Packages (Name, License, Version, CategoryID, Description, URL, SubmittedTS, ModifiedTS, SubmitterUID, MaintainerUID) VALUES (%s, %s, %s, %d, %s, %s, UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), %d, %d)",
	$dbh->quote($pkgname),
	$dbh->quote($license),
	$dbh->quote($pkgver),
	$category_id,
	$dbh->quote($pkgdesc),
	$dbh->quote($pkgurl),
	$uid,
	$uid);

	$dbh->exec($q);
}

/**
 * Update all database information for a specific package
 *
 * @param string $pkgname Name of the updated package
 * @param string $license License of the updated package
 * @param string $pkgver Version of the updated package
 * @param string $pkgdesc Description of updated package
 * @param string $pkgurl The upstream URL for the package
 * @param int $uid The user ID of the updater
 * @param int $pkgid The package ID of the updated package
 *
 * @return void
 */
function update_pkgdetails($pkgname, $license, $pkgver, $pkgdesc, $pkgurl, $uid, $pkgid) {
	$dbh = DB::connect();
	/* This is an overwrite of an existing package! */
	$q = sprintf("UPDATE Packages SET ModifiedTS = UNIX_TIMESTAMP(), Name = %s, Version = %s, License = %s, Description = %s, URL = %s, OutOfDateTS = NULL, MaintainerUID = %d WHERE ID = %d",
	$dbh->quote($pkgname),
	$dbh->quote($pkgver),
	$dbh->quote($license),
	$dbh->quote($pkgdesc),
	$dbh->quote($pkgurl),
	$uid,
	$pkgid);

	$dbh->exec($q);
}

/**
 * Add a dependency for a specific package to the database
 *
 * @param int $pkgid The package ID to add the dependency for
 * @param string $depname The name of the dependency to add
 * @param string $depcondition The  type of dependency for the package
 *
 * @return void
 */
function add_pkg_dep($pkgid, $depname, $depcondition) {
	$dbh = DB::connect();
	$q = sprintf("INSERT INTO PackageDepends (PackageID, DepName, DepCondition) VALUES (%d, %s, %s)",
	$pkgid,
	$dbh->quote($depname),
	$dbh->quote($depcondition));

	$dbh->exec($q);
}

/**
 * Add a source for a specific package to the database
 *
 * @param int $pkgid The package ID to add the source for
 * @param string $pkgsrc The package source to add to the database
 *
 * @return void
 */
function add_pkg_src($pkgid, $pkgsrc) {
	$dbh = DB::connect();
	$q = "INSERT INTO PackageSources (PackageID, Source) VALUES (";
	$q .= $pkgid . ", " . $dbh->quote($pkgsrc) . ")";

	$dbh->exec($q);
}

/**
 * Change the category a package belongs to
 *
 * @param int $pkgid The package ID to change the category for
 * @param int $category_id The new category ID for the package
 *
 * @return void
 */
function update_pkg_category($pkgid, $category_id) {
	$dbh = DB::connect();
	$q = sprintf( "UPDATE Packages SET CategoryID = %d WHERE ID = %d",
	$category_id,
	$pkgid);

	$dbh->exec($q);
}

/**
 * Remove package dependencies from a specific package
 *
 * @param string $pkgid The package ID to remove package dependencies from
 *
 * @return void
 */
function remove_pkg_deps($pkgid) {
	$dbh = DB::connect();
	$q = "DELETE FROM PackageDepends WHERE PackageID = " . $pkgid;

	$dbh->exec($q);
}

/**
 * Remove package sources from a specific package
 *
 * @param string $pkgid The package ID to remove package sources from
 *
 * @return void
 */
function remove_pkg_sources($pkgid) {
	$dbh = DB::connect();
	$q = "DELETE FROM PackageSources WHERE PackageID = " . $pkgid;

	$dbh->exec($q);
}
