<?php

include_once("pkgreqfuncs.inc.php");

/**
 * Get the number of non-deleted comments for a specific package base
 *
 * @param string $base_id The package base ID to get comment count for
 * @param bool $include_deleted True if deleted comments should be included
 * @param bool $only_pinned True if only pinned comments should be included
 *
 * @return string The number of comments left for a specific package
 */
function pkgbase_comments_count($base_id, $include_deleted, $only_pinned=false) {
	$base_id = intval($base_id);
	if (!$base_id) {
		return null;
	}

	$dbh = DB::connect();
	$q = "SELECT COUNT(*) FROM PackageComments ";
	$q.= "WHERE PackageBaseID = " . $base_id . " ";
	if (!$include_deleted) {
		$q.= "AND DelTS IS NULL";
	}
	if ($only_pinned) {
		$q.= "AND NOT PinnedTS = 0";
	}
	$result = $dbh->query($q);
	if (!$result) {
		return null;
	}

	return $result->fetchColumn(0);
}

/**
 * Get all package comment information for a specific package base
 *
 * @param int $base_id The package base ID to get comments for
 * @param int $limit Maximum number of comments to return (0 means unlimited)
 * @param bool $include_deleted True if deleted comments should be included
 * @param bool $only_pinned True when only pinned comments are to be included
 *
 * @return array All package comment information for a specific package base
 */
function pkgbase_comments($base_id, $limit, $include_deleted, $only_pinned=false) {
	$base_id = intval($base_id);
	$limit = intval($limit);
	if (!$base_id) {
		return null;
	}

	$dbh = DB::connect();
	$q = "SELECT PackageComments.ID, A.UserName AS UserName, UsersID, Comments, ";
	$q.= "PackageBaseID, CommentTS, DelTS, EditedTS, B.UserName AS EditUserName, ";
	$q.= "DelUsersID, C.UserName AS DelUserName, ";
	$q.= "PinnedTS FROM PackageComments ";
	$q.= "LEFT JOIN Users A ON PackageComments.UsersID = A.ID ";
	$q.= "LEFT JOIN Users B ON PackageComments.EditedUsersID = B.ID ";
	$q.= "LEFT JOIN Users C ON PackageComments.DelUsersID = C.ID ";
	$q.= "WHERE PackageBaseID = " . $base_id . " ";

	if (!$include_deleted) {
		$q.= "AND DelTS IS NULL ";
	}
	if ($only_pinned) {
		$q.= "AND NOT PinnedTS = 0 ";
	}
	$q.= "ORDER BY CommentTS DESC";
	if ($limit > 0) {
		$q.=" LIMIT " . $limit;
	}
	$result = $dbh->query($q);
	if (!$result) {
		return null;
	}

	return $result->fetchAll();
}

/**
 * Add a comment to a package page and send out appropriate notifications
 *
 * @param string $base_id The package base ID to add the comment on
 * @param string $uid The user ID of the individual who left the comment
 * @param string $comment The comment left on a package page
 *
 * @return void
 */
function pkgbase_add_comment($base_id, $uid, $comment) {
	$dbh = DB::connect();

	if (trim($comment) == '') {
		return array(false, __('Comment cannot be empty.'));
	}

	$q = "INSERT INTO PackageComments ";
	$q.= "(PackageBaseID, UsersID, Comments, CommentTS) VALUES (";
	$q.= intval($base_id) . ", " . $uid . ", ";
	$q.= $dbh->quote($comment) . ", " . strval(time()) . ")";
	$dbh->exec($q);
	$comment_id = $dbh->lastInsertId();

	notify(array('comment', $uid, $base_id, $comment_id));

	return array(true, __('Comment has been added.'));
}

/**
 * Pin/unpin a package comment
 *
 * @param bool $unpin True if unpinning rather than pinning
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkgbase_pin_comment($unpin=false) {
	$uid = uid_from_sid($_COOKIE["AURSID"]);

	if (!$uid) {
		return array(false, __("You must be logged in before you can edit package information."));
	}

	if (isset($_POST["comment_id"])) {
		$comment_id = $_POST["comment_id"];
	} else {
		return array(false, __("Missing comment ID."));
	}

	if (!$unpin) {
		if (pkgbase_comments_count($_POST['package_base'], false, true) >= 5){
			return array(false, __("No more than 5 comments can be pinned."));
		}
	}

	if (!can_pin_comment($comment_id)) {
		if (!$unpin) {
			return array(false, __("You are not allowed to pin this comment."));
		} else {
			return array(false, __("You are not allowed to unpin this comment."));
		}
	}

	$dbh = DB::connect();
	$q = "UPDATE PackageComments ";
	if (!$unpin) {
		$q.= "SET PinnedTS = " . strval(time()) . " ";
	} else {
		$q.= "SET PinnedTS = 0 ";
	}
	$q.= "WHERE ID = " . intval($comment_id);
	$dbh->exec($q);

	if (!$unpin) {
		return array(true, __("Comment has been pinned."));
	} else {
		return array(true, __("Comment has been unpinned."));
	}
}

/**

 * Get a list of all packages a logged-in user has voted for
 *
 * @param string $sid The session ID of the visitor
 *
 * @return array All packages the visitor has voted for
 */
function pkgbase_votes_from_sid($sid="") {
	$pkgs = array();
	if (!$sid) {return $pkgs;}
	$dbh = DB::connect();
	$q = "SELECT PackageBaseID ";
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
 * Get the package base details
 *
 * @param string $id The package base ID to get description for
 *
 * @return array The package base's details OR error message
 **/
function pkgbase_get_details($base_id) {
	$dbh = DB::connect();

	$q = "SELECT PackageBases.ID, PackageBases.Name, ";
	$q.= "PackageBases.NumVotes, PackageBases.Popularity, ";
	$q.= "PackageBases.OutOfDateTS, PackageBases.SubmittedTS, ";
	$q.= "PackageBases.ModifiedTS, PackageBases.SubmitterUID, ";
	$q.= "PackageBases.MaintainerUID, PackageBases.PackagerUID, ";
	$q.= "PackageBases.FlaggerUID, ";
	$q.= "(SELECT COUNT(*) FROM PackageRequests ";
	$q.= " WHERE PackageRequests.PackageBaseID = PackageBases.ID ";
	$q.= " AND PackageRequests.Status = 0) AS RequestCount ";
	$q.= "FROM PackageBases ";
	$q.= "WHERE PackageBases.ID = " . intval($base_id);
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
 * Display the package base details page
 *
 * @param string $id The package base ID to get details page for
 * @param array $row Package base details retrieved by pkgbase_get_details()
 * @param string $SID The session ID of the visitor
 *
 * @return void
 */
function pkgbase_display_details($base_id, $row, $SID="") {
	$dbh = DB::connect();

	if (isset($row['error'])) {
		print "<p>" . $row['error'] . "</p>\n";
	}
	else {
		$pkgbase_name = pkgbase_name_from_id($base_id);

		include('pkgbase_details.php');

		if ($SID) {
			include('pkg_comment_box.php');
		}

		$include_deleted = has_credential(CRED_COMMENT_VIEW_DELETED);

		$limit_pinned = isset($_GET['pinned']) ? 0 : 5;
		$pinned = pkgbase_comments($base_id, $limit_pinned, false, true);
		if (!empty($pinned)) {
			include('pkg_comments.php');
		}
		unset($pinned);

		$limit = isset($_GET['comments']) ? 0 : 10;
		$comments = pkgbase_comments($base_id, $limit, $include_deleted);
		if (!empty($comments)) {
			include('pkg_comments.php');
		}
	}
}

/**
 * Convert a list of package IDs into a list of corresponding package bases.
 *
 * @param array|int $ids Array of package IDs to convert
 *
 * @return array|int List of package base IDs
 */
function pkgbase_from_pkgid($ids) {
	$dbh = DB::connect();

	if (is_array($ids)) {
		$q = "SELECT PackageBaseID FROM Packages ";
		$q.= "WHERE ID IN (" . implode(",", $ids) . ")";
		$result = $dbh->query($q);
		return $result->fetchAll(PDO::FETCH_COLUMN, 0);
	} else {
		$q = "SELECT PackageBaseID FROM Packages ";
		$q.= "WHERE ID = " . $ids;
		$result = $dbh->query($q);
		return $result->fetch(PDO::FETCH_COLUMN, 0);
	}
}

/**
 * Retrieve ID of a package base by name
 *
 * @param string $name The package base name to retrieve the ID for
 *
 * @return int The ID of the package base
 */
function pkgbase_from_name($name) {
	$dbh = DB::connect();
	$q = "SELECT ID FROM PackageBases WHERE Name = " . $dbh->quote($name);
	$result = $dbh->query($q);
	return $result->fetch(PDO::FETCH_COLUMN, 0);
}

/**
 * Retrieve the name of a package base given its ID
 *
 * @param int $base_id The ID of the package base to query
 *
 * @return string The name of the package base
 */
function pkgbase_name_from_id($base_id) {
	$dbh = DB::connect();
	$q = "SELECT Name FROM PackageBases WHERE ID = " . intval($base_id);
	$result = $dbh->query($q);
	return $result->fetch(PDO::FETCH_COLUMN, 0);
}

/**
 * Get the names of all packages belonging to a package base
 *
 * @param int $base_id The ID of the package base
 *
 * @return array The names of all packages belonging to the package base
 */
function pkgbase_get_pkgnames($base_id) {
	$dbh = DB::connect();
	$q = "SELECT Name FROM Packages WHERE PackageBaseID = " . intval($base_id);
	$result = $dbh->query($q);
	return $result->fetchAll(PDO::FETCH_COLUMN, 0);
}

/**
 * Delete all packages belonging to a package base
 *
 * @param int $base_id The ID of the package base
 *
 * @return void
 */
function pkgbase_delete_packages($base_id) {
	$dbh = DB::connect();
	$q = "DELETE FROM Packages WHERE PackageBaseID = " . intval($base_id);
	$dbh->exec($q);
}

/**
 * Retrieve the maintainer of a package base given its ID
 *
 * @param int $base_id The ID of the package base to query
 *
 * @return int The user ID of the current package maintainer
 */
function pkgbase_maintainer_uid($base_id) {
	$dbh = DB::connect();
	$q = "SELECT MaintainerUID FROM PackageBases WHERE ID = " . intval($base_id);
	$result = $dbh->query($q);
	return $result->fetch(PDO::FETCH_COLUMN, 0);
}

/**
 * Retrieve the maintainers of an array of package bases given by their ID
 *
 * @param int $base_ids The array of IDs of the package bases to query
 *
 * @return int The user ID of the current package maintainer
 */
function pkgbase_maintainer_uids($base_ids) {
	$dbh = DB::connect();
	$q = "SELECT MaintainerUID FROM PackageBases WHERE ID IN (" . implode(",", $base_ids) . ")";
	$result = $dbh->query($q);
	return $result->fetchAll(PDO::FETCH_COLUMN, 0);
}

/**
 * Flag package(s) as out-of-date
 *
 * @param array $base_ids Array of package base IDs to flag/unflag
 * @param string $comment The comment to add
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkgbase_flag($base_ids, $comment) {
	if (!has_credential(CRED_PKGBASE_FLAG)) {
		return array(false, __("You must be logged in before you can flag packages."));
	}

	$base_ids = sanitize_ids($base_ids);
	if (empty($base_ids)) {
		return array(false, __("You did not select any packages to flag."));
	}

	if (strlen($comment) < 3) {
		return array(false, __("The selected packages have not been flagged, please enter a comment."));
	}

	$uid = uid_from_sid($_COOKIE['AURSID']);
	$dbh = DB::connect();

	$q = "UPDATE PackageBases SET ";
	$q.= "OutOfDateTS = " . strval(time()) . ", FlaggerUID = " . $uid . ", ";
	$q.= "FlaggerComment = " . $dbh->quote($comment) . " ";
	$q.= "WHERE ID IN (" . implode(",", $base_ids) . ") ";
	$q.= "AND OutOfDateTS IS NULL";
	$dbh->exec($q);

	foreach ($base_ids as $base_id) {
		notify(array('flag', $uid, $base_id));
	}

	return array(true, __("The selected packages have been flagged out-of-date."));
}

/**
 * Unflag package(s) as out-of-date
 *
 * @param array $base_ids Array of package base IDs to flag/unflag
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkgbase_unflag($base_ids) {
	$uid = uid_from_sid($_COOKIE["AURSID"]);
	if (!$uid) {
		return array(false, __("You must be logged in before you can unflag packages."));
	}

	$base_ids = sanitize_ids($base_ids);
	if (empty($base_ids)) {
		return array(false, __("You did not select any packages to unflag."));
	}

	$dbh = DB::connect();

	$q = "UPDATE PackageBases SET ";
	$q.= "OutOfDateTS = NULL ";
	$q.= "WHERE ID IN (" . implode(",", $base_ids) . ") ";

	$maintainers = array_merge(pkgbase_maintainer_uids($base_ids), pkgbase_get_comaintainer_uids($base_ids));
	if (!has_credential(CRED_PKGBASE_UNFLAG, $maintainers)) {
		$q.= "AND (MaintainerUID = " . $uid . " OR FlaggerUID = " . $uid. ")";
	}

	$result = $dbh->exec($q);

	if ($result) {
		return array(true, __("The selected packages have been unflagged."));
	}
}

/**
 * Get package flag OOD comment
 *
 * @param int $base_id
 *
 * @return array Tuple of pkgbase ID, reason for OOD, and user who flagged
 */
function pkgbase_get_flag_comment($base_id) {
	$base_id = intval($base_id);
	$dbh = DB::connect();

	$q = "SELECT FlaggerComment,OutOfDateTS,Username FROM PackageBases ";
	$q.= "LEFT JOIN Users ON FlaggerUID = Users.ID ";
	$q.= "WHERE PackageBases.ID = " . $base_id . " ";
	$q.= "AND PackageBases.OutOfDateTS IS NOT NULL";
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
 * Delete package bases
 *
 * @param array $base_ids Array of package base IDs to delete
 * @param int $merge_base_id Package base to merge the deleted ones into
 * @param int $via Package request to close upon deletion
 * @param bool $grant Allow anyone to delete the package base
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkgbase_delete ($base_ids, $merge_base_id, $via, $grant=false) {
	if (!$grant && !has_credential(CRED_PKGBASE_DELETE)) {
		return array(false, __("You do not have permission to delete packages."));
	}

	$base_ids = sanitize_ids($base_ids);
	if (empty($base_ids)) {
		return array(false, __("You did not select any packages to delete."));
	}

	$dbh = DB::connect();

	if ($merge_base_id) {
		$merge_base_name = pkgbase_name_from_id($merge_base_id);
	}

	$uid = uid_from_sid($_COOKIE['AURSID']);
	foreach ($base_ids as $base_id) {
		if ($merge_base_id) {
			notify(array('delete', $uid, $base_id, $merge_base_id));
		} else {
			notify(array('delete', $uid, $base_id));
		}
	}

	/*
	 * Close package request if the deletion was initiated through the
	 * request interface. NOTE: This needs to happen *before* the actual
	 * deletion. Otherwise, the former maintainer will not be included in
	 * the Cc list of the request notification email.
	 */
	if ($via) {
		pkgreq_close(intval($via), 'accepted', '');
	}

	/* Scan through pending deletion requests and close them. */
	if (!$action) {
		$username = username_from_sid($_COOKIE['AURSID']);
		foreach ($base_ids as $base_id) {
			$pkgreq_ids = array_merge(pkgreq_by_pkgbase($base_id));
			foreach ($pkgreq_ids as $pkgreq_id) {
				pkgreq_close(intval($pkgreq_id), 'accepted',
					'The user ' .  $username .
					' deleted the package.', true);
			}
		}
	}

	if ($merge_base_id) {
		/* Merge comments */
		$q = "UPDATE PackageComments ";
		$q.= "SET PackageBaseID = " . intval($merge_base_id) . " ";
		$q.= "WHERE PackageBaseID IN (" . implode(",", $base_ids) . ")";
		$dbh->exec($q);

		/* Merge notifications */
		$q = "SELECT DISTINCT UserID FROM PackageNotifications cn ";
		$q.= "WHERE PackageBaseID IN (" . implode(",", $base_ids) . ") ";
		$q.= "AND NOT EXISTS (SELECT * FROM PackageNotifications cn2 ";
		$q.= "WHERE cn2.PackageBaseID = " . intval($merge_base_id) . " ";
		$q.= "AND cn2.UserID = cn.UserID)";
		$result = $dbh->query($q);

		while ($notify_uid = $result->fetch(PDO::FETCH_COLUMN, 0)) {
			$q = "INSERT INTO PackageNotifications (UserID, PackageBaseID) ";
			$q.= "VALUES (" . intval($notify_uid) . ", " . intval($merge_base_id) . ")";
			$dbh->exec($q);
		}

		/* Merge votes */
		foreach ($base_ids as $base_id) {
			$q = "UPDATE PackageVotes ";
			$q.= "SET PackageBaseID = " . intval($merge_base_id) . " ";
			$q.= "WHERE PackageBaseID = " . $base_id . " ";
			$q.= "AND UsersID NOT IN (";
			$q.= "SELECT * FROM (SELECT UsersID ";
			$q.= "FROM PackageVotes ";
			$q.= "WHERE PackageBaseID = " . intval($merge_base_id);
			$q.= ") temp)";
			$dbh->exec($q);
		}

		$q = "UPDATE PackageBases ";
		$q.= "SET NumVotes = (SELECT COUNT(*) FROM PackageVotes ";
		$q.= "WHERE PackageBaseID = " . intval($merge_base_id) . ") ";
		$q.= "WHERE ID = " . intval($merge_base_id);
		$dbh->exec($q);
	}

	$q = "DELETE FROM Packages WHERE PackageBaseID IN (" . implode(",", $base_ids) . ")";
	$dbh->exec($q);

	$q = "DELETE FROM PackageBases WHERE ID IN (" . implode(",", $base_ids) . ")";
	$dbh->exec($q);

	return array(true, __("The selected packages have been deleted."));
}

/**
 * Adopt or disown packages
 *
 * @param array $base_ids Array of package base IDs to adopt/disown
 * @param bool $action Adopts if true, disowns if false. Adopts by default
 * @param int $via Package request to close upon adoption
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkgbase_adopt ($base_ids, $action=true, $via) {
	$dbh = DB::connect();

	$uid = uid_from_sid($_COOKIE["AURSID"]);
	if (!$uid) {
		if ($action) {
			return array(false, __("You must be logged in before you can adopt packages."));
		} else {
			return array(false, __("You must be logged in before you can disown packages."));
		}
	}

	/* Verify package ownership. */
	$base_ids = sanitize_ids($base_ids);

	$q = "SELECT ID FROM PackageBases ";
	$q.= "WHERE ID IN (" . implode(",", $base_ids) . ") ";

	if ($action && !has_credential(CRED_PKGBASE_ADOPT)) {
		/* Regular users may only adopt orphan packages. */
		$q.= "AND MaintainerUID IS NULL";
	}
	if (!$action && !has_credential(CRED_PKGBASE_DISOWN)) {
		/* Regular users may only disown their own packages. */
		$q.= "AND MaintainerUID = " . $uid;
	}

	$result = $dbh->query($q);
	$base_ids = $result->fetchAll(PDO::FETCH_COLUMN, 0);

	/* Error out if the list of remaining packages is empty. */
	if (empty($base_ids)) {
		if ($action) {
			return array(false, __("You did not select any packages to adopt."));
		} else {
			return array(false, __("You did not select any packages to disown."));
		}
	}

	/*
	 * Close package request if the disownment was initiated through the
	 * request interface. NOTE: This needs to happen *before* the actual
	 * disown operation. Otherwise, the former maintainer will not be
	 * included in the Cc list of the request notification email.
	 */
	if ($via) {
		pkgreq_close(intval($via), 'accepted', '');
	}

	/* Scan through pending orphan requests and close them. */
	if (!$action) {
		$username = username_from_sid($_COOKIE['AURSID']);
		foreach ($base_ids as $base_id) {
			$pkgreq_ids = pkgreq_by_pkgbase($base_id, 'orphan');
			foreach ($pkgreq_ids as $pkgreq_id) {
				pkgreq_close(intval($pkgreq_id), 'accepted',
					'The user ' .  $username .
					' disowned the package.', true);
			}
		}
	}

	/* Adopt or disown the package. */
	if ($action) {
		$q = "UPDATE PackageBases ";
		$q.= "SET MaintainerUID = $uid ";
		$q.= "WHERE ID IN (" . implode(",", $base_ids) . ") ";
		$dbh->exec($q);

		/* Add the new maintainer to the notification list. */
		pkgbase_notify($base_ids);
	} else {
		/* Update the co-maintainer list when disowning a package. */
		if (has_credential(CRED_PKGBASE_DISOWN)) {
			foreach ($base_ids as $base_id) {
				pkgbase_set_comaintainers($base_id, array());
			}

			$q = "UPDATE PackageBases ";
			$q.= "SET MaintainerUID = NULL ";
			$q.= "WHERE ID IN (" . implode(",", $base_ids) . ") ";
			$dbh->exec($q);
		} else {
			foreach ($base_ids as $base_id) {
				$comaintainers = pkgbase_get_comaintainers($base_id);

				if (count($comaintainers) > 0) {
					$uid = uid_from_username($comaintainers[0]);
					$comaintainers = array_diff($comaintainers, array($comaintainers[0]));
					pkgbase_set_comaintainers($base_id, $comaintainers);
				} else {
					$uid = "NULL";
				}

				$q = "UPDATE PackageBases ";
				$q.= "SET MaintainerUID = " . $uid .  " ";
				$q.= "WHERE ID = " . $base_id;
				$dbh->exec($q);
			}
		}
	}

	foreach ($base_ids as $base_id) {
		notify(array($action ? 'adopt' : 'disown', $base_id, $uid));
	}

	if ($action) {
		return array(true, __("The selected packages have been adopted."));
	} else {
		return array(true, __("The selected packages have been disowned."));
	}
}

/**
 * Vote and un-vote for packages
 *
 * @param array $base_ids Array of package base IDs to vote/un-vote
 * @param bool $action Votes if true, un-votes if false. Votes by default
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkgbase_vote ($base_ids, $action=true) {
	if (!has_credential(CRED_PKGBASE_VOTE)) {
		if ($action) {
			return array(false, __("You must be logged in before you can vote for packages."));
		} else {
			return array(false, __("You must be logged in before you can un-vote for packages."));
		}
	}

	$base_ids = sanitize_ids($base_ids);
	if (empty($base_ids)) {
		if ($action) {
			return array(false, __("You did not select any packages to vote for."));
		} else {
			return array(false, __("Your votes have been removed from the selected packages."));
		}
	}

	$dbh = DB::connect();
	$my_votes = pkgbase_votes_from_sid($_COOKIE["AURSID"]);
	$uid = uid_from_sid($_COOKIE["AURSID"]);

	$first = 1;
	foreach ($base_ids as $pid) {
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
					$vote_clauses = "($uid, $pid, " . strval(time()) . ")";
				}
			} else {
				$vote_ids .= ", $pid";
				if ($action) {
					$vote_clauses .= ", ($uid, $pid, " . strval(time()) . ")";
				}
			}
		}
	}

	/* Only add votes for packages the user hasn't already voted for. */
	$op = $action ? "+" : "-";
	$q = "UPDATE PackageBases SET NumVotes = NumVotes $op 1 ";
	$q.= "WHERE ID IN ($vote_ids)";

	$dbh->exec($q);

	if ($action) {
		$q = "INSERT INTO PackageVotes (UsersID, PackageBaseID, VoteTS) VALUES ";
		$q.= $vote_clauses;
	} else {
		$q = "DELETE FROM PackageVotes WHERE UsersID = $uid ";
		$q.= "AND PackageBaseID IN ($vote_ids)";
	}

	$dbh->exec($q);

	if ($action) {
		return array(true, __("Your votes have been cast for the selected packages."));
	} else {
		return array(true, __("Your votes have been removed from the selected packages."));
	}
}

/**
 * Get all usernames and IDs that voted for a specific package base
 *
 * @param string $pkgbase_name The package base to retrieve votes for
 *
 * @return array User IDs and usernames that voted for a specific package base
 */
function pkgbase_votes_from_name($pkgbase_name) {
	$dbh = DB::connect();

	$q = "SELECT UsersID, Username, Name, VoteTS FROM PackageVotes ";
	$q.= "LEFT JOIN Users ON UsersID = Users.ID ";
	$q.= "LEFT JOIN PackageBases ";
	$q.= "ON PackageVotes.PackageBaseID = PackageBases.ID ";
	$q.= "WHERE PackageBases.Name = ". $dbh->quote($pkgbase_name) . " ";
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
 * Determine if a user has already voted for a specific package base
 *
 * @param string $uid The user ID to check for an existing vote
 * @param string $base_id The package base ID to check for an existing vote
 *
 * @return bool True if the user has already voted, otherwise false
 */
function pkgbase_user_voted($uid, $base_id) {
	$dbh = DB::connect();
	$q = "SELECT COUNT(*) FROM PackageVotes WHERE ";
	$q.= "UsersID = ". $dbh->quote($uid) . " AND ";
	$q.= "PackageBaseID = " . $dbh->quote($base_id);
	$result = $dbh->query($q);
	if (!$result) {
		return null;
	}

	return ($result->fetch(PDO::FETCH_COLUMN, 0) > 0);
}

/**
 * Determine if a user wants notifications for a specific package base
 *
 * @param string $uid User ID to check in the database
 * @param string $base_id Package base ID to check notifications for
 *
 * @return bool True if the user wants notifications, otherwise false
 */
function pkgbase_user_notify($uid, $base_id) {
	$dbh = DB::connect();

	$q = "SELECT * FROM PackageNotifications WHERE UserID = " . $dbh->quote($uid);
	$q.= " AND PackageBaseID = " . $dbh->quote($base_id);
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
 * @param array $base_ids Array of package base IDs to toggle
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkgbase_notify ($base_ids, $action=true) {
	if (!has_credential(CRED_PKGBASE_NOTIFY)) {
		return;
	}

	$base_ids = sanitize_ids($base_ids);
	if (empty($base_ids)) {
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
	foreach ($base_ids as $bid) {
		$q = "SELECT Name FROM PackageBases WHERE ID = $bid";
		$result = $dbh->query($q);
		if ($result) {
			$row = $result->fetch(PDO::FETCH_NUM);
			$basename = $row[0];
		}
		else {
			$basename = '';
		}

		if ($first)
			$first = false;
		else
			$output .= ", ";


		if ($action) {
			$q = "SELECT COUNT(*) FROM PackageNotifications WHERE ";
			$q .= "UserID = $uid AND PackageBaseID = $bid";

			/* Notification already added. Don't add again. */
			$result = $dbh->query($q);
			if ($result->fetchColumn() == 0) {
				$q = "INSERT INTO PackageNotifications (PackageBaseID, UserID) VALUES ($bid, $uid)";
				$dbh->exec($q);
			}

			$output .= $basename;
		}
		else {
			$q = "DELETE FROM PackageNotifications WHERE PackageBaseID = $bid ";
			$q .= "AND UserID = $uid";
			$dbh->exec($q);

			$output .= $basename;
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
 * @param  boolean $undelete True if undeleting rather than deleting
 * @return array Tuple of success/failure indicator and error message
 */
function pkgbase_delete_comment($undelete=false) {
	$uid = uid_from_sid($_COOKIE["AURSID"]);
	if (!$uid) {
		return array(false, __("You must be logged in before you can edit package information."));
	}

	if (isset($_POST["comment_id"])) {
		$comment_id = $_POST["comment_id"];
	} else {
		return array(false, __("Missing comment ID."));
	}

	$dbh = DB::connect();
	if ($undelete) {
		if (!has_credential(CRED_COMMENT_UNDELETE)) {
			return array(false, __("You are not allowed to undelete this comment."));
		}

		$q = "UPDATE PackageComments ";
		$q.= "SET DelUsersID = NULL, ";
		$q.= "DelTS = NULL ";
		$q.= "WHERE ID = ".intval($comment_id);
		$dbh->exec($q);
		return array(true, __("Comment has been undeleted."));
	} else {
		if (!can_delete_comment($comment_id)) {
			return array(false, __("You are not allowed to delete this comment."));
		}

		$q = "UPDATE PackageComments ";
		$q.= "SET DelUsersID = ".$uid.", ";
		$q.= "DelTS = " . strval(time()) . " ";
		$q.= "WHERE ID = ".intval($comment_id);
		$dbh->exec($q);
		return array(true, __("Comment has been deleted."));
	}
}

/**
 * Edit a package comment
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkgbase_edit_comment($comment) {
	$uid = uid_from_sid($_COOKIE["AURSID"]);
	if (!$uid) {
		return array(false, __("You must be logged in before you can edit package information."));
	}

	if (isset($_POST["comment_id"])) {
		$comment_id = $_POST["comment_id"];
	} else {
		return array(false, __("Missing comment ID."));
	}

	if (trim($comment) == '') {
		return array(false, __('Comment cannot be empty.'));
	}

	$dbh = DB::connect();
	if (can_edit_comment($comment_id)) {
		$q = "UPDATE PackageComments ";
		$q.= "SET EditedUsersID = ".$uid.", ";
		$q.= "Comments = ".$dbh->quote($comment).", ";
		$q.= "EditedTS = " . strval(time()) . " ";
		$q.= "WHERE ID = ".intval($comment_id);
		$dbh->exec($q);
		return array(true, __("Comment has been edited."));
	} else {
		return array(false, __("You are not allowed to edit this comment."));
	}
}

/**
 * Get a list of package base keywords
 *
 * @param int $base_id The package base ID to retrieve the keywords for
 *
 * @return array An array of keywords
 */
function pkgbase_get_keywords($base_id) {
	$dbh = DB::connect();
	$q = "SELECT Keyword FROM PackageKeywords ";
	$q .= "WHERE PackageBaseID = " . intval($base_id) . " ";
	$q .= "ORDER BY Keyword ASC";
	$result = $dbh->query($q);

	if ($result) {
		return $result->fetchAll(PDO::FETCH_COLUMN, 0);
	} else {
		return array();
	}
}

/**
 * Update the list of keywords of a package base
 *
 * @param int $base_id The package base ID to update the keywords of
 * @param array $users Array of keywords
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkgbase_set_keywords($base_id, $keywords) {
	$base_id = intval($base_id);

	$maintainers = array_merge(array(pkgbase_maintainer_uid($base_id)), pkgbase_get_comaintainer_uids(array($base_id)));
	if (!has_credential(CRED_PKGBASE_SET_KEYWORDS, $maintainers)) {
		return array(false, __("You are not allowed to edit the keywords of this package base."));
	}

	/* Remove empty and duplicate user names. */
	$keywords = array_unique(array_filter(array_map('trim', $keywords)));

	$dbh = DB::connect();

	$q = sprintf("DELETE FROM PackageKeywords WHERE PackageBaseID = %d", $base_id);
	$dbh->exec($q);

	$i = 0;
	foreach ($keywords as $keyword) {
		$q = sprintf("INSERT INTO PackageKeywords (PackageBaseID, Keyword) VALUES (%d, %s)", $base_id, $dbh->quote($keyword));
		$dbh->exec($q);

		$i++;
		if ($i >= 20) {
			break;
		}
	}

	return array(true, __("The package base keywords have been updated."));
}

/**
 * Get a list of package base co-maintainers
 *
 * @param int $base_id The package base ID to retrieve the co-maintainers for
 *
 * @return array An array of co-maintainer user names
 */
function pkgbase_get_comaintainers($base_id) {
	$dbh = DB::connect();
	$q = "SELECT UserName FROM PackageComaintainers ";
	$q .= "INNER JOIN Users ON Users.ID = PackageComaintainers.UsersID ";
	$q .= "WHERE PackageComaintainers.PackageBaseID = " . intval($base_id) . " ";
	$q .= "ORDER BY Priority ASC";
	$result = $dbh->query($q);

	if ($result) {
		return $result->fetchAll(PDO::FETCH_COLUMN, 0);
	} else {
		return array();
	}
}

/**
 * Get a list of package base co-maintainer IDs
 *
 * @param int $base_id The package base ID to retrieve the co-maintainers for
 *
 * @return array An array of co-maintainer user UDs
 */
function pkgbase_get_comaintainer_uids($base_ids) {
	$dbh = DB::connect();
	$q = "SELECT UsersID FROM PackageComaintainers ";
	$q .= "INNER JOIN Users ON Users.ID = PackageComaintainers.UsersID ";
	$q .= "WHERE PackageComaintainers.PackageBaseID IN (" . implode(",", $base_ids) . ") ";
	$q .= "ORDER BY Priority ASC";
	$result = $dbh->query($q);

	if ($result) {
		return $result->fetchAll(PDO::FETCH_COLUMN, 0);
	} else {
		return array();
	}
}

/**
 * Update the list of co-maintainers of a package base
 *
 * @param int $base_id The package base ID to update the co-maintainers of
 * @param array $users Array of co-maintainer user names
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkgbase_set_comaintainers($base_id, $users) {
	if (!has_credential(CRED_PKGBASE_EDIT_COMAINTAINERS, array(pkgbase_maintainer_uid($base_id)))) {
		return array(false, __("You are not allowed to manage co-maintainers of this package base."));
	}

	/* Remove empty and duplicate user names. */
	$users = array_unique(array_filter(array_map('trim', $users)));

	$dbh = DB::connect();

	$uids_new = array();
	foreach($users as $user) {
		$q = "SELECT ID FROM Users ";
		$q .= "WHERE UserName = " . $dbh->quote($user);
		$result = $dbh->query($q);
		$uid = $result->fetchColumn(0);

		if (!$uid) {
			return array(false, __("Invalid user name: %s", $user));
		}

		$uids_new[] = $uid;
	}

	$q = sprintf("SELECT UsersID FROM PackageComaintainers WHERE PackageBaseID = %d", $base_id);
	$result = $dbh->query($q);
	$uids_old = $result->fetchAll(PDO::FETCH_COLUMN, 0);

	$uids_add = array_diff($uids_new, $uids_old);
	$uids_rem = array_diff($uids_old, $uids_new);

	$i = 1;
	foreach ($uids_new as $uid) {
		if (in_array($uid, $uids_add)) {
			$q = sprintf("INSERT INTO PackageComaintainers (PackageBaseID, UsersID, Priority) VALUES (%d, %d, %d)", $base_id, $uid, $i);
			notify(array('comaintainer-add', $base_id, $uid));
		} else {
			$q = sprintf("UPDATE PackageComaintainers SET Priority = %d WHERE PackageBaseID = %d AND UsersID = %d", $i, $base_id, $uid);
		}

		$dbh->exec($q);
		$i++;
	}

	foreach ($uids_rem as $uid) {
		$q = sprintf("DELETE FROM PackageComaintainers WHERE PackageBaseID = %d AND UsersID = %d", $base_id, $uid);
		$dbh->exec($q);
		notify(array('comaintainer-remove', $base_id, $uid));
	}

	return array(true, __("The package base co-maintainers have been updated."));
}
