<?php

include_once("confparser.inc.php");
include_once("pkgbasefuncs.inc.php");

/**
 * Get the number of package requests
 *
 * @return int The total number of package requests
 */
function pkgreq_count() {
	$dbh = DB::connect();
	$q = "SELECT COUNT(*) FROM PackageRequests";
	return $dbh->query($q)->fetchColumn();
}

/**
 * Get a list of all package requests
 *
 * @param int $offset The index of the first request to return
 * @param int $limit The maximum number of requests to return
 *
 * @return array List of pacakge requests with details
 */
function pkgreq_list($offset, $limit) {
	$dbh = DB::connect();

	$q = "SELECT PackageRequests.ID, ";
	$q.= "PackageRequests.PackageBaseID AS BaseID, ";
	$q.= "PackageRequests.PackageBaseName AS Name, ";
	$q.= "PackageRequests.MergeBaseName AS MergeInto, ";
	$q.= "RequestTypes.Name AS Type, PackageRequests.Comments, ";
	$q.= "Users.Username AS User, PackageRequests.RequestTS, ";
	$q.= "PackageRequests.Status, PackageRequests.Status = 0 AS Open ";
	$q.= "FROM PackageRequests INNER JOIN RequestTypes ON ";
	$q.= "RequestTypes.ID = PackageRequests.ReqTypeID ";
	$q.= "INNER JOIN Users ON Users.ID = PackageRequests.UsersID ";
	$q.= "ORDER BY Open DESC, RequestTS DESC ";
	$q.= "LIMIT " . $limit . " OFFSET " . $offset;

	return $dbh->query($q)->fetchAll();
}

/**
 * Get a list of all open package requests belonging to a certain package base
 *
 * @param int $baseid The package base ID to retrieve requests for
 * @param int $type The type of requests to obtain
 *
 * @return array List of package request IDs
 */
function pkgreq_by_pkgbase($baseid, $type=false) {
	$dbh = DB::connect();

	$q = "SELECT PackageRequests.ID ";
	$q.= "FROM PackageRequests INNER JOIN RequestTypes ON ";
	$q.= "RequestTypes.ID = PackageRequests.ReqTypeID ";
	$q.= "WHERE PackageRequests.Status = 0 ";
	$q.= "AND PackageRequests.PackageBaseID = " . intval($baseid);

	if ($type) {
		$q .= " AND RequestTypes.Name = " . $dbh->quote($type);
	}

	return $dbh->query($q)->fetchAll(PDO::FETCH_COLUMN, 0);
}

/**
 * Obtain the package base that belongs to a package request.
 *
 * @param int $id Package request ID to retrieve the package base for
 *
 * @return int The name of the corresponding package base
 */
function pkgreq_get_pkgbase_name($id) {
	$dbh = DB::connect();

	$q = "SELECT PackageBaseName FROM PackageRequests ";
	$q.= "WHERE ID = " . intval($id);
	$result = $dbh->query($q);
	return $result->fetch(PDO::FETCH_COLUMN, 0);
}

/**
 * Obtain the email address of the creator of a package request
 *
 * @param int $id Package request ID to retrieve the creator for
 *
 * @return int The email address of the creator
 */
function pkgreq_get_creator_email($id) {
	$dbh = DB::connect();

	$q = "SELECT Email FROM Users INNER JOIN PackageRequests ";
	$q.= "ON Users.ID = PackageRequests.UsersID ";
	$q.= "WHERE PackageRequests.ID = " . intval($id);
	$result = $dbh->query($q);
	return $result->fetch(PDO::FETCH_COLUMN, 0);
}

/**
 * File a deletion/orphan request against a package base
 *
 * @param string $ids The package base IDs to file the request against
 * @param string $type The type of the request
 * @param string $merge_into The target of a merge operation
 * @param string $comments The comments to be added to the request
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkgreq_file($ids, $type, $merge_into, $comments) {
	if (!has_credential(CRED_PKGREQ_FILE)) {
		return array(false, __("You must be logged in to file package requests."));
	}

	if (!empty($merge_into) && !preg_match("/^[a-z0-9][a-z0-9\.+_-]*$/D", $merge_into)) {
		return array(false, __("Invalid name: only lowercase letters are allowed."));
	}

	if (!empty($merge_into) && !pkgbase_from_name($merge_into)) {
		return array(false, __("Cannot find package to merge votes and comments into."));
	}

	if (empty($comments)) {
		return array(false, __("The comment field must not be empty."));
	}

	$dbh = DB::connect();
	$uid = uid_from_sid($_COOKIE["AURSID"]);

	/* TODO: Allow for filing multiple requests at once. */
	$base_id = intval($ids[0]);
	$pkgbase_name = pkgbase_name_from_id($base_id);

	if ($merge_into == $pkgbase_name) {
		return array(false, __("Cannot merge a package base with itself."));
	}

	$q = "SELECT ID FROM RequestTypes WHERE Name = " . $dbh->quote($type);
	$result = $dbh->query($q);
	if ($row = $result->fetch(PDO::FETCH_ASSOC)) {
		$type_id = $row['ID'];
	} else {
		return array(false, __("Invalid request type."));
	}

	$q = "INSERT INTO PackageRequests ";
	$q.= "(ReqTypeID, PackageBaseID, PackageBaseName, MergeBaseName, ";
	$q.= "UsersID, Comments, RequestTS) VALUES (" . $type_id . ", ";
	$q.= $base_id . ", " .  $dbh->quote($pkgbase_name) . ", ";
	$q.= $dbh->quote($merge_into) . ", " . $uid . ", ";
	$q.= $dbh->quote($comments) . ", " . strval(time()) . ")";
	$dbh->exec($q);
	$request_id = $dbh->lastInsertId();

	/* Send e-mail notifications. */
	$params = array('request-open', $uid, $request_id, $type, $base_id);
	if ($type === 'merge') {
		$params[] = $merge_into;
	}
	notify($params);

	$auto_orphan_age = config_get('options', 'auto_orphan_age');
	$auto_delete_age = config_get('options', 'auto_delete_age');
	$details = pkgbase_get_details($base_id);
	if ($type == 'orphan' && $details['OutOfDateTS'] > 0 &&
	    time() - $details['OutOfDateTS'] >= $auto_orphan_age &&
	    $auto_orphan_age > 0) {
		/*
		 * Close package request. NOTE: This needs to happen *before*
		 * the actual disown operation. Otherwise, the former
		 * maintainer will not be included in the Cc list of the
		 * request notification email.
		 */
		$out_of_date_time = gmdate("Y-m-d", intval($details["OutOfDateTS"]));
		pkgreq_close($request_id, "accepted",
			     "The package base has been flagged out-of-date " .
			     "since " . $out_of_date_time . ".", true);
		$q = "UPDATE PackageBases SET MaintainerUID = NULL ";
		$q.= "WHERE ID = " . $base_id;
		$dbh->exec($q);
	} else if ($type == 'deletion' && $details['MaintainerUID'] == $uid &&
	    $details['SubmittedTS'] > 0 && $auto_delete_age > 0 &&
	    time() - $details['SubmittedTS'] <= $auto_delete_age) {
		/*
		 * Close package request. NOTE: This needs to happen *before*
		 * the actual deletion operation. Otherwise, the former
		 * maintainer will not be included in the Cc list of the
		 * request notification email.
		 */
		pkgreq_close($request_id, "accepted",
			     "Deletion of a fresh package requested by its " .
			     "current maintainer.", true);
		pkgbase_delete(array($base_id), NULL, NULL, true);
	}

	return array(true, __("Added request successfully."));
}

/**
 * Close a deletion/orphan request
 *
 * @param int $id The package request to close
 * @param string $reason Whether the request was accepted or rejected
 * @param string $comments Comments to be added to the notification email
 * @param boolean $auto_close (optional) Whether the request is auto-closed
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkgreq_close($id, $reason, $comments, $auto_close=false) {
	switch ($reason) {
	case 'accepted':
		$status = 2;
		break;
	case 'rejected':
		$status = 3;
		break;
	default:
		return array(false, __("Invalid reason."));
	}

	$dbh = DB::connect();
	$id = intval($id);
	$uid = $auto_close ? 0 : uid_from_sid($_COOKIE["AURSID"]);

	if (!$auto_close && !has_credential(CRED_PKGREQ_CLOSE)) {
		return array(false, __("Only TUs and developers can close requests."));
	}

	$q = "UPDATE PackageRequests SET Status = " . intval($status) . ", ";
	$q.= "ClosureComment = " . $dbh->quote($comments) . " ";
	$q.= "WHERE ID = " . intval($id);
	$dbh->exec($q);

	/* Send e-mail notifications. */
	notify(array('request-close', $uid, $id, $reason));

	return array(true, __("Request closed successfully."));
}
