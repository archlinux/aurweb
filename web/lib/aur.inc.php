<?php
set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../template');
header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-cache, must-revalidate');
header('Expires: Tue, 11 Oct 1988 22:00:00 GMT'); // quite a special day
header('Pragma: no-cache');

date_default_timezone_set('UTC');

include_once('translator.inc.php');
set_lang();

include_once("config.inc.php");
include_once("DB.class.php");
include_once("routing.inc.php");
include_once("version.inc.php");
include_once("acctfuncs.inc.php");
include_once("cachefuncs.inc.php");

/**
 * Check if a visitor is logged in
 *
 * Query "Sessions" table with supplied cookie. Determine if the cookie is valid
 * or not. Unset the cookie if invalid or session timeout reached. Update the
 * session timeout if it is still valid.
 *
 * @global array $_COOKIE User cookie values
 * @global string $LOGIN_TIMEOUT Time until session times out
 * @param \PDO $dbh Already established database connection
 *
 * @return void
 */
function check_sid($dbh=NULL) {
	global $_COOKIE;
	global $LOGIN_TIMEOUT;

	if (isset($_COOKIE["AURSID"])) {
		$failed = 0;
		# the visitor is logged in, try and update the session
		#
		if(!$dbh) {
			$dbh = DB::connect();
		}
		$q = "SELECT LastUpdateTS, UNIX_TIMESTAMP() FROM Sessions ";
		$q.= "WHERE SessionID = " . $dbh->quote($_COOKIE["AURSID"]);
		$result = $dbh->query($q);
		$row = $result->fetch(PDO::FETCH_NUM);

		if (!$row[0]) {
			# Invalid SessionID - hacker alert!
			#
			$failed = 1;
		} else {
			$last_update = $row[0];
			if ($last_update + $LOGIN_TIMEOUT <= $row[1]) {
				$failed = 2;
			}
		}

		if ($failed == 1) {
			# clear out the hacker's cookie, and send them to a naughty page
			# why do you have to be so harsh on these people!?
			#
			setcookie("AURSID", "", 1, "/", null, !empty($_SERVER['HTTPS']), true);
			unset($_COOKIE['AURSID']);
		} elseif ($failed == 2) {
			# session id timeout was reached and they must login again.
			#
			delete_session_id($_COOKIE["AURSID"], $dbh);

			setcookie("AURSID", "", 1, "/", null, !empty($_SERVER['HTTPS']), true);
			unset($_COOKIE['AURSID']);
		} else {
			# still logged in and haven't reached the timeout, go ahead
			# and update the idle timestamp

			# Only update the timestamp if it is less than the
			# current time plus $LOGIN_TIMEOUT.
			#
			# This keeps 'remembered' sessions from being
			# overwritten.
			if ($last_update < time() + $LOGIN_TIMEOUT) {
				$q = "UPDATE Sessions SET LastUpdateTS = UNIX_TIMESTAMP() ";
				$q.= "WHERE SessionID = " . $dbh->quote($_COOKIE["AURSID"]);
				$dbh->exec($q);
			}
		}
	}
	return;
}

/**
 * Verify the supplied CSRF token matches expected token
 *
 * @return bool True if the CSRF token is the same as the cookie SID, otherwise false
 */
function check_token() {
	if (isset($_POST['token']) && isset($_COOKIE['AURSID'])) {
		return ($_POST['token'] == $_COOKIE['AURSID']);
	} else {
		return false;
	}
}

/**
 * Verify a user supplied e-mail against RFC 3696 and DNS records
 *
 * @param string $addy E-mail address being validated in foo@example.com format
 *
 * @return bool True if e-mail passes validity checks, otherwise false
 */
function valid_email($addy) {
	// check against RFC 3696
	if (filter_var($addy, FILTER_VALIDATE_EMAIL) === false) {
		return false;
	}

	// check dns for mx, a, aaaa records
	list($local, $domain) = explode('@', $addy);
	if (!(checkdnsrr($domain, 'MX') || checkdnsrr($domain, 'A') || checkdnsrr($domain, 'AAAA'))) {
		return false;
	}

	return true;
}

/**
 * Generate a unique session ID
 *
 * @return string MD5 hash of the concatenated user IP, random number, and current time
 */
function new_sid() {
	return md5($_SERVER['REMOTE_ADDR'] . uniqid(mt_rand(), true));
}

/**
 * Determine the user's username in the database using a user ID
 *
 * @param string $id User's ID
 * @param \PDO $dbh Already established database connection
 *
 * @return string Username if it exists, otherwise "None"
 */
function username_from_id($id="", $dbh=NULL) {
	if (!$id) {
		return "";
	}
	if(!$dbh) {
		$dbh = DB::connect();
	}
	$q = "SELECT Username FROM Users WHERE ID = " . $dbh->quote($id);
	$result = $dbh->query($q);
	if (!$result) {
		return "None";
	}
	$row = $result->fetch(PDO::FETCH_NUM);

	return $row[0];
}

/**
 * Determine the user's username in the database using a session ID
 *
 * @param string $sid User's session ID
 * @param \PDO $dbh Already established database connection
 *
 * @return string Username of the visitor
 */
function username_from_sid($sid="", $dbh=NULL) {
	if (!$sid) {
		return "";
	}
	if(!$dbh) {
		$dbh = DB::connect();
	}
	$q = "SELECT Username ";
	$q.= "FROM Users, Sessions ";
	$q.= "WHERE Users.ID = Sessions.UsersID ";
	$q.= "AND Sessions.SessionID = " . $dbh->quote($sid);
	$result = $dbh->query($q);
	if (!$result) {
		return "";
	}
	$row = $result->fetch(PDO::FETCH_NUM);

	return $row[0];
}

/**
 * Determine the user's e-mail address in the database using a session ID
 *
 * @param string $sid User's session ID
 * @param \PDO $dbh Already established database connection
 *
 * @return string User's e-mail address as given during registration
 */
function email_from_sid($sid="", $dbh=NULL) {
	if (!$sid) {
		return "";
	}
	if(!$dbh) {
		$dbh = DB::connect();
	}
	$q = "SELECT Email ";
	$q.= "FROM Users, Sessions ";
	$q.= "WHERE Users.ID = Sessions.UsersID ";
	$q.= "AND Sessions.SessionID = " . $dbh->quote($sid);
	$result = $dbh->query($q);
	if (!$result) {
		return "";
	}
	$row = $result->fetch(PDO::FETCH_NUM);

	return $row[0];
}

/**
 * Determine the user's account type in the database using a session ID
 *
 * @param string $sid User's session ID
 * @param \PDO $dbh Already established database connection
 *
 * @return string Account type of user ("User", "Trusted User", or "Developer")
 */
function account_from_sid($sid="", $dbh=NULL) {
	if (!$sid) {
		return "";
	}
	if(!$dbh) {
		$dbh = DB::connect();
	}
	$q = "SELECT AccountType ";
	$q.= "FROM Users, AccountTypes, Sessions ";
	$q.= "WHERE Users.ID = Sessions.UsersID ";
	$q.= "AND AccountTypes.ID = Users.AccountTypeID ";
	$q.= "AND Sessions.SessionID = " . $dbh->quote($sid);
	$result = $dbh->query($q);
	if (!$result) {
		return "";
	}
	$row = $result->fetch(PDO::FETCH_NUM);

	return $row[0];
}

/**
 * Determine the user's ID in the database using a session ID
 *
 * @param string $sid User's session ID
 * @param \PDO $dbh Already established database connection
 *
 * @return string|int The user's name, 0 on query failure
 */
function uid_from_sid($sid="", $dbh=NULL) {
	if (!$sid) {
		return "";
	}
	if(!$dbh) {
		$dbh = DB::connect();
	}
	$q = "SELECT Users.ID ";
	$q.= "FROM Users, Sessions ";
	$q.= "WHERE Users.ID = Sessions.UsersID ";
	$q.= "AND Sessions.SessionID = " . $dbh->quote($sid);
	$result = $dbh->query($q);
	if (!$result) {
		return 0;
	}
	$row = $result->fetch(PDO::FETCH_NUM);

	return $row[0];
}

/**
 * Common AUR header displayed on all pages
 *
 * @global string $LANG Language selected by the visitor
 * @global array $SUPPORTED_LANGS Languages that are supported by the AUR
 * @param string $title Name of the AUR page to be displayed on browser
 *
 * @return void
 */
function html_header($title="", $details=array()) {
	global $AUR_LOCATION;
	global $DISABLE_HTTP_LOGIN;
	global $LANG;
	global $SUPPORTED_LANGS;

	include('header.php');
	return;
}

/**
 * Common AUR footer displayed on all pages
 *
 * @param string $ver The AUR version
 *
 * @return void
 */
function html_footer($ver="") {
	include('footer.php');
	return;
}

/**
 * Determine if a user has permission to submit a package
 *
 * @param string $name Name of the package to be submitted
 * @param string $sid User's session ID
 * @param \PDO $dbh Already established database connection
 *
 * @return int 0 if the user can't submit, 1 if the user can submit
 */
function can_submit_pkg($name="", $sid="", $dbh=NULL) {
	if (!$name || !$sid) {return 0;}
	if(!$dbh) {
		$dbh = DB::connect();
	}
	$q = "SELECT MaintainerUID ";
	$q.= "FROM Packages WHERE Name = " . $dbh->quote($name);
	$result = $dbh->query($q);
	$row = $result->fetch(PDO::FETCH_NUM);

	if (!$row[0]) {
		return 1;
	}
	$my_uid = uid_from_sid($sid, $dbh);

	if ($row[0] === NULL || $row[0] == $my_uid) {
		return 1;
	}

	return 0;
}

/**
 * Recursively delete a directory
 *
 * @param string $dirname Name of the directory to be removed
 *
 * @return void
 */
function rm_tree($dirname) {
	if (empty($dirname) || !is_dir($dirname)) return;

	foreach (scandir($dirname) as $item) {
		if ($item != '.' && $item != '..') {
			$path = $dirname . '/' . $item;
			if (is_file($path) || is_link($path)) {
				unlink($path);
			}
			else {
				rm_tree($path);
			}
		}
	}

	rmdir($dirname);

	return;
}

 /**
 * Determine the user's ID in the database using a username
 *
 * @param string $username The username of an account
 * @param \PDO $dbh Already established database connection
 *
 * @return string Return user ID if exists for username, otherwise "None"
 */
function uid_from_username($username="", $dbh=NULL) {
	if (!$username) {
		return "";
	}
	if(!$dbh) {
		$dbh = DB::connect();
	}
	$q = "SELECT ID FROM Users WHERE Username = " . $dbh->quote($username);
	$result = $dbh->query($q);
	if (!$result) {
		return "None";
	}
	$row = $result->fetch(PDO::FETCH_NUM);

	return $row[0];
}

/**
 * Determine the user's ID in the database using an e-mail address
 *
 * @param string $email An e-mail address in foo@example.com format
 * @param \PDO $dbh Already established database connection
 *
 * @return string The user's ID
 */
function uid_from_email($email="", $dbh=NULL) {
	if (!$email) {
		return "";
	}
	if(!$dbh) {
		$dbh = DB::connect();
	}
	$q = "SELECT ID FROM Users WHERE Email = " . $dbh->quote($email);
	$result = $dbh->query($q);
	if (!$result) {
		return "None";
	}
	$row = $result->fetch(PDO::FETCH_NUM);

	return $row[0];
}

/**
 * Determine if a user has TU or Developer privileges
 *
 * @return bool Return true if the user is a TU or developer, otherwise false
 */
function check_user_privileges() {
	$type = account_from_sid($_COOKIE['AURSID']);
	return ($type == 'Trusted User' || $type == 'Developer');
}

/**
 * Generate clean url with edited/added user values
 *
 * Makes a clean string of variables for use in URLs based on current $_GET and
 * list of values to edit/add to that. Any empty variables are discarded.
 *
 * @example print "http://example.com/test.php?" . mkurl("foo=bar&bar=baz")
 *
 * @param string $append string of variables and values formatted as in URLs
 *
 * @return string clean string of variables to append to URL, urlencoded
 */
function mkurl($append) {
	$get = $_GET;
	$append = explode('&', $append);
	$uservars = array();
	$out = '';

	foreach ($append as $i) {
		$ex = explode('=', $i);
		$uservars[$ex[0]] = $ex[1];
	}

	foreach ($uservars as $k => $v) { $get[$k] = $v; }

	foreach ($get as $k => $v) {
		if ($v !== '') {
			$out .= '&amp;' . urlencode($k) . '=' . urlencode($v);
		}
	}

	return substr($out, 5);
}

/**
 * Determine a user's salt from the database
 *
 * @param string $user_id The user ID of the user trying to log in
 * @param \PDO $dbh Already established database connection
 *
 * @return string|void Return the salt for the requested user, otherwise void
 */
function get_salt($user_id, $dbh=NULL) {
	if(!$dbh) {
		$dbh = DB::connect();
	}
	$q = "SELECT Salt FROM Users WHERE ID = " . $user_id;
	$result = $dbh->query($q);
	if ($result) {
		$row = $result->fetch(PDO::FETCH_NUM);
		return $row[0];
	}
	return;
}

/**
 * Save a user's salted password in the database
 *
 * @param string $user_id The user ID of the user who is salting their password
 * @param string $passwd The password of the user logging in
 * @param \PDO $dbh Already established database connection
 */
function save_salt($user_id, $passwd, $dbh=NULL) {
	if(!$dbh) {
		$dbh = DB::connect();
	}
	$salt = generate_salt();
	$hash = salted_hash($passwd, $salt);
	$q = "UPDATE Users SET Salt = " . $dbh->quote($salt) . ", ";
	$q.= "Passwd = " . $dbh->quote($hash) . " WHERE ID = " . $user_id;
	$result = $dbh->exec($q);
}

/**
 * Generate a string to be used for salting passwords
 *
 * @return string MD5 hash of concatenated random number and current time
 */
function generate_salt() {
	return md5(uniqid(mt_rand(), true));
}

/**
 * Combine salt and password to form a hash
 *
 * @param string $passwd User plaintext password
 * @param string $salt MD5 hash to be used as user salt
 *
 * @return string The MD5 hash of the concatenated salt and user password
 */
function salted_hash($passwd, $salt) {
	if (strlen($salt) != 32) {
		trigger_error('Salt does not look like an md5 hash', E_USER_WARNING);
	}
	return md5($salt . $passwd);
}

/**
 * Process submitted comments so any links can be followed
 *
 * @param string $comment Raw user submitted package comment
 *
 * @return string User comment with links printed in HTML
 */
function parse_comment($comment) {
	$url_pattern = '/(\b(?:https?|ftp):\/\/[\w\/\#~:.?+=&%@!\-;,]+?' .
		'(?=[.:?\-;,]*(?:[^\w\/\#~:.?+=&%@!\-;,]|$)))/iS';

	$matches = preg_split($url_pattern, $comment, -1,
		PREG_SPLIT_DELIM_CAPTURE);

	$html = '';
	for ($i = 0; $i < count($matches); $i++) {
		if ($i % 2) {
			# convert links
			$html .= '<a href="' . htmlspecialchars($matches[$i]) .
				'">' .	htmlspecialchars($matches[$i]) . '</a>';
		}
		else {
			# convert everything else
			$html .= nl2br(htmlspecialchars($matches[$i]));
		}
	}

	return $html;
}

/**
 * Wrapper for beginning a database transaction
 *
 * @param \PDO $dbh Already established database connection
 */
function begin_atomic_commit($dbh=NULL) {
	if(!$dbh) {
		$dbh = DB::connect();
	}
	$dbh->beginTransaction();
}

/**
 * Wrapper for committing a database transaction
 *
 * @param \PDO $dbh Already established database connection
 */
function end_atomic_commit($dbh=NULL) {
	if(!$dbh) {
		$dbh = DB::connect();
	}
	$dbh->commit();
}

/**
 *
 * Determine the row ID for the most recently insterted row
 *
 * @param \PDO $dbh Already established database connection
 *
 * @return string The ID of the last inserted row
 */
function last_insert_id($dbh=NULL) {
	if(!$dbh) {
		$dbh = DB::connect();
	}
	return $dbh->lastInsertId();
}

/**
 * Determine package information for latest package
 *
 * @param int $numpkgs Number of packages to get information on
 * @param \PDO $dbh Already established database connection
 *
 * @return array $packages Package info for the specified number of recent packages
 */
function latest_pkgs($numpkgs, $dbh=NULL) {
	if(!$dbh) {
		$dbh = DB::connect();
	}

	$q = "SELECT * FROM Packages ";
	$q.= "ORDER BY SubmittedTS DESC ";
	$q.= "LIMIT " .intval($numpkgs);
	$result = $dbh->query($q);

	if ($result) {
		while ($row = $result->fetch(PDO::FETCH_ASSOC)) {
			$packages[] = $row;
		}
	}

	return $packages;
}
