<?php
include_once("config.inc.php");
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
 * @global string $AUR_LOCATION The AUR's URL used for notification e-mails
 * @global string $AUR_REQUEST_ML The request notification mailing list
 * @param string $ids The package base IDs to file the request against
 * @param string $type The type of the request
 * @param string $merge_into The target of a merge operation
 * @param string $comments The comments to be added to the request
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkgreq_file($ids, $type, $merge_into, $comments) {
	global $AUR_LOCATION;
	global $AUR_REQUEST_ML;

	if (!empty($merge_into) && !preg_match("/^[a-z0-9][a-z0-9\.+_-]*$/", $merge_into)) {
		return array(false, __("Invalid name: only lowercase letters are allowed."));
	}

	if (empty($comments)) {
		return array(false, __("The comment field must not be empty."));
	}

	$dbh = DB::connect();
	$uid = uid_from_sid($_COOKIE["AURSID"]);

	/* TODO: Allow for filing multiple requests at once. */
	$base_id = $ids[0];
	$pkgbase_name = pkgbase_name_from_id($base_id);

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
	$q.= intval($base_id) . ", " .  $dbh->quote($pkgbase_name) . ", ";
	$q.= $dbh->quote($merge_into) . ", " . $uid . ", ";
	$q.= $dbh->quote($comments) . ", UNIX_TIMESTAMP())";
	$dbh->exec($q);
	$request_id = $dbh->lastInsertId();

	/*
	 * Send e-mail notifications.
	 * TODO: Move notification logic to separate function where it belongs.
	 */
	$cc = array(pkgreq_get_creator_email($request_id));

	$q = "SELECT Users.Email ";
	$q.= "FROM Users INNER JOIN PackageBases ";
	$q.= "ON PackageBases.MaintainerUID = Users.ID ";
	$q.= "WHERE PackageBases.ID = " . intval($base_id);
	$result = $dbh->query($q);
	if ($row = $result->fetch(PDO::FETCH_ASSOC)) {
		$cc[] = $row['Email'];
	}

	$q = "SELECT Name FROM PackageBases WHERE ID = ";
	$q.= intval($base_id);
	$result = $dbh->query($q);
	$row = $result->fetch(PDO::FETCH_ASSOC);

	/*
	 * TODO: Add native language emails for users, based on their
	 * preferences. Simply making these strings translatable won't
	 * work, users would be getting emails in the language that the
	 * user who posted the comment was in.
	 */
	$username = username_from_sid($_COOKIE['AURSID']);
	$body =
		$username . " [1] filed a " . $type . " request for " .
		$row['Name'] . " [2]:\n\n" . $comments . "\n\n" .
		"[1] " . $AUR_LOCATION . get_user_uri($username) . "\n" .
		"[2] " . $AUR_LOCATION . get_pkgbase_uri($row['Name']) . "\n";
	$body = wordwrap($body, 70);
	$headers = "MIME-Version: 1.0\r\n" .
		   "Content-type: text/plain; charset=UTF-8\r\n" .
		   "Cc: " . implode(', ', $cc) . "\r\n";
	$thread_id = "<pkg-request-" . $request_id . "@aur.archlinux.org>";
	$headers .= "From: notify@aur.archlinux.org\r\n" .
		    "Message-ID: $thread_id\r\n" .
		    "X-Mailer: AUR";
	@mail($AUR_REQUEST_ML, "[PRQ#" . $request_id . "] " . ucfirst($type) .
			       " Request for " .  $row['Name'], $body,
			       $headers);

	return array(true, __("Added request successfully."));
}

/**
 * Close a deletion/orphan request
 *
 * @global string $AUR_LOCATION The AUR's URL used for notification e-mails
 * @global string $AUR_REQUEST_ML The request notification mailing list
 * @param int $id The package request to close
 * @param string $reason Whether the request was accepted or rejected
 * @param string $comments Comments to be added to the notification email
 *
 * @return array Tuple of success/failure indicator and error message
 */
function pkgreq_close($id, $reason, $comments) {
	global $AUR_LOCATION;
	global $AUR_REQUEST_ML;

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

	if (!has_credential(CRED_PKGREQ_CLOSE)) {
		return array(false, __("Only TUs and developers can close requests."));
	}

	$q = "UPDATE PackageRequests SET Status = " . intval($status) . " ";
	$q.= "WHERE ID = " . intval($id);
	$dbh->exec($q);

	/*
	 * Send e-mail notifications.
	 * TODO: Move notification logic to separate function where it belongs.
	 */
	$cc = array(pkgreq_get_creator_email($id));

	$q = "SELECT Users.Email ";
	$q.= "FROM Users INNER JOIN PackageBases ";
	$q.= "ON PackageBases.MaintainerUID = Users.ID ";
	$q.= "INNER JOIN PackageRequests ";
	$q.= "ON PackageRequests.PackageBaseID = PackageBases.ID ";
	$q.= "WHERE PackageRequests.ID = " . $id;
	$result = $dbh->query($q);
	if ($row = $result->fetch(PDO::FETCH_ASSOC)) {
		$cc[] = $row['Email'];
	}

	/*
	 * TODO: Add native language emails for users, based on their
	 * preferences. Simply making these strings translatable won't
	 * work, users would be getting emails in the language that the
	 * user who posted the comment was in.
	 */
	$username = username_from_sid($_COOKIE['AURSID']);
	$body = "Request #" . intval($id) . " has been " . $reason . " by " .
		$username . " [1]";
	if (!empty(trim($comments))) {
		$body .= ":\n\n" . $comments . "\n\n";
	} else {
		$body .= ".\n\n";
	}
	$body .= "[1] " . $AUR_LOCATION . get_user_uri($username) . "\n";
	$body = wordwrap($body, 70);
	$headers = "MIME-Version: 1.0\r\n" .
		   "Content-type: text/plain; charset=UTF-8\r\n" .
		   "Cc: " . implode(', ', $cc) . "\r\n";
	$thread_id = "<pkg-request-" . $id . "@aur.archlinux.org>";
	$headers .= "From: notify@aur.archlinux.org\r\n" .
		    "In-Reply-To: $thread_id\r\n" .
		    "References: $thread_id\r\n" .
		    "X-Mailer: AUR";
	@mail($AUR_REQUEST_ML, "[PRQ#" . $id . "] Request " . ucfirst($reason),
	      $body, $headers);

	return array(true, __("Request closed successfully."));
}
