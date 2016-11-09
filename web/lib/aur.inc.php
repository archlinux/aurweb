<?php
set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../template');
header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-cache, must-revalidate');
header('Expires: Tue, 11 Oct 1988 22:00:00 GMT'); // quite a special day
header('Pragma: no-cache');

date_default_timezone_set('UTC');

include_once('translator.inc.php');
set_lang();

include_once("DB.class.php");
include_once("routing.inc.php");
include_once("version.inc.php");
include_once("acctfuncs.inc.php");
include_once("cachefuncs.inc.php");
include_once("confparser.inc.php");
include_once("credentials.inc.php");

/**
 * Check if a visitor is logged in
 *
 * Query "Sessions" table with supplied cookie. Determine if the cookie is valid
 * or not. Unset the cookie if invalid or session timeout reached. Update the
 * session timeout if it is still valid.
 *
 * @global array $_COOKIE User cookie values
 *
 * @return void
 */
function check_sid() {
	global $_COOKIE;

	if (isset($_COOKIE["AURSID"])) {
		$failed = 0;
		$timeout = config_get_int('options', 'login_timeout');
		# the visitor is logged in, try and update the session
		#
		$dbh = DB::connect();
		$q = "SELECT LastUpdateTS, " . strval(time()) . " FROM Sessions ";
		$q.= "WHERE SessionID = " . $dbh->quote($_COOKIE["AURSID"]);
		$result = $dbh->query($q);
		$row = $result->fetch(PDO::FETCH_NUM);

		if (!$row[0]) {
			# Invalid SessionID - hacker alert!
			#
			$failed = 1;
		} else {
			$last_update = $row[0];
			if ($last_update + $timeout <= $row[1]) {
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
			delete_session_id($_COOKIE["AURSID"]);

			setcookie("AURSID", "", 1, "/", null, !empty($_SERVER['HTTPS']), true);
			unset($_COOKIE['AURSID']);
		} else {
			# still logged in and haven't reached the timeout, go ahead
			# and update the idle timestamp

			# Only update the timestamp if it is less than the
			# current time plus $timeout.
			#
			# This keeps 'remembered' sessions from being
			# overwritten.
			if ($last_update < time() + $timeout) {
				$q = "UPDATE Sessions SET LastUpdateTS = " . strval(time()) . " ";
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
 *
 * @return string Username if it exists, otherwise null
 */
function username_from_id($id) {
	$id = intval($id);

	$dbh = DB::connect();
	$q = "SELECT Username FROM Users WHERE ID = " . $dbh->quote($id);
	$result = $dbh->query($q);
	if (!$result) {
		return null;
	}

	$row = $result->fetch(PDO::FETCH_NUM);
	return $row[0];
}

/**
 * Determine the user's username in the database using a session ID
 *
 * @param string $sid User's session ID
 *
 * @return string Username of the visitor
 */
function username_from_sid($sid="") {
	if (!$sid) {
		return "";
	}
	$dbh = DB::connect();
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
 * Format a user name for inclusion in HTML data
 *
 * @param string $username The user name to format
 *
 * @return string The generated HTML code for the account link
 */
function html_format_username($username) {
	$username_fmt = $username ? htmlspecialchars($username, ENT_QUOTES) : __("None");

	if ($username && isset($_COOKIE["AURSID"])) {
		$link = '<a href="' . get_uri('/account/') . $username_fmt;
		$link .= '" title="' . __('View account information for %s', $username_fmt);
		$link .= '">' . $username_fmt . '</a>';
		return $link;
	} else {
		return $username_fmt;
	}
}

/**
 * Format the maintainer and co-maintainers for inclusion in HTML data
 *
 * @param string $maintainer The user name of the maintainer
 * @param array $comaintainers The list of co-maintainer user names
 *
 * @return string The generated HTML code for the account links
 */
function html_format_maintainers($maintainer, $comaintainers) {
	$code = html_format_username($maintainer);

	if (count($comaintainers) > 0) {
		$code .= ' (';
		foreach ($comaintainers as $comaintainer) {
			$code .= html_format_username($comaintainer);
			if ($comaintainer !== end($comaintainers)) {
				$code .= ', ';
			}
		}
		$code .= ')';
	}

	return $code;
}

/**
 * Format a link in the package actions box
 *
 * @param string $uri The link target
 * @param string $inner The HTML code to use for the link label
 *
 * @return string The generated HTML code for the action link
 */
function html_action_link($uri, $inner) {
	if (isset($_COOKIE["AURSID"])) {
		$code = '<a href="' . htmlspecialchars($uri, ENT_QUOTES) . '">';
	} else {
		$code = '<a href="' . get_uri('/login/', true) . '?referer=';
		$code .= urlencode(rtrim(aur_location(), '/') . $uri) . '">';
	}
	$code .= $inner . '</a>';

	return $code;
}

/**
 * Format a form in the package actions box
 *
 * @param string $uri The link target
 * @param string $action The action name (passed as HTTP POST parameter)
 * @param string $inner The HTML code to use for the link label
 *
 * @return string The generated HTML code for the action link
 */
function html_action_form($uri, $action, $inner) {
	if (isset($_COOKIE["AURSID"])) {
		$code = '<form action="' . htmlspecialchars($uri, ENT_QUOTES) . '" ';
		$code .= 'method="post">';
		$code .= '<input type="hidden" name="token" value="';
		$code .= htmlspecialchars($_COOKIE['AURSID'], ENT_QUOTES) . '" />';
		$code .= '<input type="submit" class="button text-button" name="';
		$code .= htmlspecialchars($action, ENT_QUOTES) . '" ';
		$code .= 'value="' . $inner . '" />';
		$code .= '</form>';
	} else {
		$code = '<a href="' . get_uri('/login/', true) . '">';
		$code .= $inner . '</a>';
	}

	return $code;
}

/**
 * Determine the user's e-mail address in the database using a session ID
 *
 * @param string $sid User's session ID
 *
 * @return string User's e-mail address as given during registration
 */
function email_from_sid($sid="") {
	if (!$sid) {
		return "";
	}
	$dbh = DB::connect();
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
 *
 * @return string Account type of user ("User", "Trusted User", or "Developer")
 */
function account_from_sid($sid="") {
	if (!$sid) {
		return "";
	}
	$dbh = DB::connect();
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
 *
 * @return string|int The user's name, 0 on query failure
 */
function uid_from_sid($sid="") {
	if (!$sid) {
		return "";
	}
	$dbh = DB::connect();
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
 *
 * @return int 0 if the user can't submit, 1 if the user can submit
 */
function can_submit_pkgbase($name="", $sid="") {
	if (!$name || !$sid) {return 0;}
	$dbh = DB::connect();
	$q = "SELECT MaintainerUID ";
	$q.= "FROM PackageBases WHERE Name = " . $dbh->quote($name);
	$result = $dbh->query($q);
	$row = $result->fetch(PDO::FETCH_NUM);

	if (!$row[0]) {
		return 1;
	}
	$my_uid = uid_from_sid($sid);

	if ($row[0] === NULL || $row[0] == $my_uid) {
		return 1;
	}

	return 0;
}

/**
 * Determine if a package can be overwritten by some package base
 *
 * @param string $name Name of the package to be submitted
 * @param int $base_id The ID of the package base
 *
 * @return bool True if the package can be overwritten, false if not
 */
function can_submit_pkg($name, $base_id) {
	$dbh = DB::connect();
	$q = "SELECT COUNT(*) FROM Packages WHERE ";
	$q.= "Name = " . $dbh->quote($name) . " AND ";
	$q.= "PackageBaseID <> " . intval($base_id);
	$result = $dbh->query($q);

	if (!$result) return false;
	return ($result->fetchColumn() == 0);
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
 *
 * @return string Return user ID if exists for username, otherwise null
 */
function uid_from_username($username) {
	$dbh = DB::connect();
	$q = "SELECT ID FROM Users WHERE Username = " . $dbh->quote($username);
	$result = $dbh->query($q);
	if (!$result) {
		return null;
	}

	$row = $result->fetch(PDO::FETCH_NUM);
	return $row[0];
}

/**
 * Determine the user's ID in the database using a username or email address
 *
 * @param string $username The username or email address of an account
 *
 * @return string Return user ID if exists, otherwise null
 */
function uid_from_loginname($loginname) {
	$uid = uid_from_username($loginname);
	if (!$uid) {
		$uid = uid_from_email($loginname);
	}
	return $uid;
}

/**
 * Determine the user's ID in the database using an e-mail address
 *
 * @param string $email An e-mail address in foo@example.com format
 *
 * @return string The user's ID
 */
function uid_from_email($email) {
	$dbh = DB::connect();
	$q = "SELECT ID FROM Users WHERE Email = " . $dbh->quote($email);
	$result = $dbh->query($q);
	if (!$result) {
		return null;
	}

	$row = $result->fetch(PDO::FETCH_NUM);
	return $row[0];
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
 *
 * @return string|void Return the salt for the requested user, otherwise void
 */
function get_salt($user_id) {
	$dbh = DB::connect();
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
 */
function save_salt($user_id, $passwd) {
	$dbh = DB::connect();
	$salt = generate_salt();
	$hash = salted_hash($passwd, $salt);
	$q = "UPDATE Users SET Salt = " . $dbh->quote($salt) . ", ";
	$q.= "Passwd = " . $dbh->quote($hash) . " WHERE ID = " . $user_id;
	return $dbh->exec($q);
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
 * Get a package comment
 *
 * @param  int $comment_id The ID of the comment
 *
 * @return array The user ID and comment OR null, null in case of an error
 */
function comment_by_id($comment_id) {
	$dbh = DB::connect();
	$q = "SELECT UsersID, Comments FROM PackageComments ";
	$q.= "WHERE ID = " . intval($comment_id);
	$result = $dbh->query($q);
	if (!$result) {
		return array(null, null);
	}

	return $result->fetch(PDO::FETCH_NUM);
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
				'" rel="nofollow">' .	htmlspecialchars($matches[$i]) . '</a>';
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
 */
function begin_atomic_commit() {
	$dbh = DB::connect();
	$dbh->beginTransaction();
}

/**
 * Wrapper for committing a database transaction
 */
function end_atomic_commit() {
	$dbh = DB::connect();
	$dbh->commit();
}

/**
 * Merge pkgbase and package options
 *
 * Merges entries of the first and the second array. If any key appears in both
 * arrays and the corresponding value in the second array is either a non-array
 * type or a non-empty array, the value from the second array replaces the
 * value from the first array. If the value from the second array is an array
 * containing a single empty string, the value in the resulting array becomes
 * an empty array instead. If the value in the second array is empty, the
 * resulting array contains the value from the first array.
 *
 * @param array $pkgbase_info Options from the pkgbase section
 * @param array $section_info Options from the package section
 *
 * @return array Merged information from both sections
 */
function array_pkgbuild_merge($pkgbase_info, $section_info) {
	$pi = $pkgbase_info;
	foreach ($section_info as $opt_key => $opt_val) {
		if (is_array($opt_val)) {
			if ($opt_val == array('')) {
				$pi[$opt_key] = array();
			} elseif (count($opt_val) > 0) {
				$pi[$opt_key] = $opt_val;
			}
		} else {
			$pi[$opt_key] = $opt_val;
		}
	}
	return $pi;
}

/**
 * Bound an integer value between two values
 *
 * @param int $n Integer value to bound
 * @param int $min Lower bound
 * @param int $max Upper bound
 *
 * @return int Bounded integer value
 */
function bound($n, $min, $max) {
	return min(max($n, $min), $max);
}

/**
 * Return the URL of the AUR root
 *
 * @return string The URL of the AUR root
 */
function aur_location() {
	$location = config_get('options', 'aur_location');
	if (substr($location, -1) != '/') {
		$location .= '/';
	}
	return $location;
}
