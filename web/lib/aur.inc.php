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
include_once("version.inc.php");
include_once("acctfuncs.inc.php");
include_once("cachefuncs.inc.php");

# see if the visitor is already logged in
#
function check_sid($dbh=NULL) {
	global $_COOKIE;
	global $LOGIN_TIMEOUT;

	if (isset($_COOKIE["AURSID"])) {
		$failed = 0;
		# the visitor is logged in, try and update the session
		#
		if(!$dbh) {
			$dbh = db_connect();
		}
		$q = "SELECT LastUpdateTS, UNIX_TIMESTAMP() FROM Sessions ";
		$q.= "WHERE SessionID = '" . db_escape_string($_COOKIE["AURSID"]) . "'";
		$result = db_query($q, $dbh);
		if (mysql_num_rows($result) == 0) {
			# Invalid SessionID - hacker alert!
			#
			$failed = 1;
		} else {
			$row = mysql_fetch_row($result);
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
			$q = "DELETE FROM Sessions WHERE SessionID = '";
			$q.= db_escape_string($_COOKIE["AURSID"]) . "'";
			db_query($q, $dbh);

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
				$q.= "WHERE SessionID = '".db_escape_string($_COOKIE["AURSID"])."'";
				db_query($q, $dbh);
			}
		}
	}
	return;
}

# verify that an email address looks like it is legitimate
#
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

# a new seed value for mt_srand()
#
function make_seed() {
	list($usec, $sec) = explode(' ', microtime());
	return (float) $sec + ((float) $usec * 10000);
}

# generate a (hopefully) unique session id
#
function new_sid() {
	return md5($_SERVER['REMOTE_ADDR'] . uniqid(mt_rand(), true));
}


# obtain the username if given their Users.ID
#
function username_from_id($id="", $dbh=NULL) {
	if (!$id) {
		return "";
	}
	if(!$dbh) {
		$dbh = db_connect();
	}
	$q = "SELECT Username FROM Users WHERE ID = " . db_escape_string($id);
	$result = db_query($q, $dbh);
	if (!$result) {
		return "None";
	}
	$row = mysql_fetch_row($result);

	return $row[0];
}


# obtain the username if given their current SID
#
function username_from_sid($sid="", $dbh=NULL) {
	if (!$sid) {
		return "";
	}
	if(!$dbh) {
		$dbh = db_connect();
	}
	$q = "SELECT Username ";
	$q.= "FROM Users, Sessions ";
	$q.= "WHERE Users.ID = Sessions.UsersID ";
	$q.= "AND Sessions.SessionID = '" . db_escape_string($sid) . "'";
	$result = db_query($q, $dbh);
	if (!$result) {
		return "";
	}
	$row = mysql_fetch_row($result);

	return $row[0];
}

# obtain the email address if given their current SID
#
function email_from_sid($sid="", $dbh=NULL) {
	if (!$sid) {
		return "";
	}
	if(!$dbh) {
		$dbh = db_connect();
	}
	$q = "SELECT Email ";
	$q.= "FROM Users, Sessions ";
	$q.= "WHERE Users.ID = Sessions.UsersID ";
	$q.= "AND Sessions.SessionID = '" . db_escape_string($sid) . "'";
	$result = db_query($q, $dbh);
	if (!$result) {
		return "";
	}
	$row = mysql_fetch_row($result);

	return $row[0];
}

# obtain the account type if given their current SID
# Return either "", "User", "Trusted User", "Developer"
#
function account_from_sid($sid="", $dbh=NULL) {
	if (!$sid) {
		return "";
	}
	if(!$dbh) {
		$dbh = db_connect();
	}
	$q = "SELECT AccountType ";
	$q.= "FROM Users, AccountTypes, Sessions ";
	$q.= "WHERE Users.ID = Sessions.UsersID ";
	$q.= "AND AccountTypes.ID = Users.AccountTypeID ";
	$q.= "AND Sessions.SessionID = '" . db_escape_string($sid) . "'";
	$result = db_query($q, $dbh);
	if (!$result) {
		return "";
	}
	$row = mysql_fetch_row($result);

	return $row[0];
}

# obtain the Users.ID if given their current SID
#
function uid_from_sid($sid="", $dbh=NULL) {
	if (!$sid) {
		return "";
	}
	if(!$dbh) {
		$dbh = db_connect();
	}
	$q = "SELECT Users.ID ";
	$q.= "FROM Users, Sessions ";
	$q.= "WHERE Users.ID = Sessions.UsersID ";
	$q.= "AND Sessions.SessionID = '" . db_escape_string($sid) . "'";
	$result = db_query($q, $dbh);
	if (!$result) {
		return 0;
	}
	$row = mysql_fetch_row($result);

	return $row[0];
}

# connect to the database
#
function db_connect() {
	$handle = mysql_connect(AUR_db_host, AUR_db_user, AUR_db_pass);
	if (!$handle) {
		die("Error connecting to AUR database: " . mysql_error());
	}

	mysql_select_db(AUR_db_name, $handle) or
		die("Error selecting AUR database: " . mysql_error());

	db_query("SET NAMES 'utf8' COLLATE 'utf8_general_ci';", $handle);

	return $handle;
}

# Escape strings for SQL query usage.
# Wraps the database driver's provided method (for convenience and porting).
function db_escape_string($string) {
	return mysql_real_escape_string($string);
}

# Escape strings for usage in SQL LIKE operators.
function db_escape_like($string) {
	return addcslashes(mysql_real_escape_string($string), '%_');
}

# disconnect from the database
# this won't normally be needed as PHP/reference counting will take care of
# closing the connection once it is no longer referenced
#
function db_disconnect($db_handle="") {
	if ($db_handle) {
		mysql_close($db_handle);
		return TRUE;
	}
	return FALSE;
}

# wrapper function around db_query in case we want to put
# query logging/debugging in.
#
function db_query($query="", $db_handle="") {
	if (!$query) {
		return FALSE;
	}

	if (!$db_handle) {
		die("DB handle was not provided to db_query");
	}

	if (defined('SQL_DEBUG') && SQL_DEBUG == 1) {
		$bt = debug_backtrace();
		error_log("DEBUG: ".$bt[0]['file'].":".$bt[0]['line']." query: $query\n");
	}

	$result = @mysql_query($query, $db_handle);
	if (!$result) {
		$bt = debug_backtrace();
		error_log("ERROR: near ".$bt[0]['file'].":".$bt[0]['line']." in query: $query\n -> ".mysql_error($db_handle));
	}

	return $result;
}

# common header
#
function html_header($title="") {
	global $_SERVER;
	global $_COOKIE;
	global $_POST;
	global $LANG;
	global $SUPPORTED_LANGS;
	global $DISABLE_HTTP_LOGIN;
	global $AUR_LOCATION;

	if (!$DISABLE_HTTP_LOGIN || (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'])) {
		$login = try_login();
		$login_error = $login['error'];
	}

	$title = htmlspecialchars($title, ENT_QUOTES);

	include('header.php');
	return;
}


# common footer
#
function html_footer($ver="") {
	include('footer.php');
	return;
}

# check to see if the user can submit a package
#
function can_submit_pkg($name="", $sid="", $dbh=NULL) {
	if (!$name || !$sid) {return 0;}
	if(!$dbh) {
		$dbh = db_connect();
	}
	$q = "SELECT MaintainerUID ";
	$q.= "FROM Packages WHERE Name = '".db_escape_string($name)."'";
	$result = db_query($q, $dbh);
	if (mysql_num_rows($result) == 0) {return 1;}
	$row = mysql_fetch_row($result);
	$my_uid = uid_from_sid($sid, $dbh);

	if ($row[0] === NULL || $row[0] == $my_uid) {
		return 1;
	}

	return 0;
}

# recursive delete directory
#
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

# Recursive chmod to set group write permissions
#
function chmod_group($path) {
	if (!is_dir($path))
		return chmod($path, 0664);

	$d = dir($path);
	while ($f = $d->read()) {
		if ($f != '.' && $f != '..') {
			$fullpath = $path.'/'.$f;
			if (is_link($fullpath))
				continue;
			elseif (!is_dir($fullpath)) {
				if (!chmod($fullpath, 0664))
					return FALSE;
			}
			elseif(!chmod_group($fullpath))
				return FALSE;
		}
	}
	$d->close();

	if(chmod($path, 0775))
		return TRUE;
	else
		return FALSE;
}

# obtain the uid given a Users.Username
#
function uid_from_username($username="", $dbh=NULL) {
	if (!$username) {
		return "";
	}
	if(!$dbh) {
		$dbh = db_connect();
	}
	$q = "SELECT ID FROM Users WHERE Username = '".db_escape_string($username)
				."'";
	$result = db_query($q, $dbh);
	if (!$result) {
		return "None";
	}
	$row = mysql_fetch_row($result);

	return $row[0];
}

# obtain the uid given a Users.Email
#
function uid_from_email($email="", $dbh=NULL) {
	if (!$email) {
		return "";
	}
	if(!$dbh) {
		$dbh = db_connect();
	}
	$q = "SELECT ID FROM Users WHERE Email = '".db_escape_string($email)
				."'";
	$result = db_query($q, $dbh);
	if (!$result) {
		return "None";
	}
	$row = mysql_fetch_row($result);

	return $row[0];
}

# check user privileges
#
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
 * ex. print "http://example.com/test.php?" . mkurl("foo=bar&bar=baz")
 *
 * @param string $append string of variables and values formatted as in URLs
 * ex. mkurl("foo=bar&bar=baz")
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

function get_salt($user_id, $dbh=NULL) {
	if(!$dbh) {
		$dbh = db_connect();
	}
	$salt_q = "SELECT Salt FROM Users WHERE ID = " . $user_id;
	$result = db_query($salt_q, $dbh);
	if ($result) {
		$salt_row = mysql_fetch_row($result);
		return $salt_row[0];
	}
	return;
}

function save_salt($user_id, $passwd, $dbh=NULL) {
	if(!$dbh) {
		$dbh = db_connect();
	}
	$salt = generate_salt();
	$hash = salted_hash($passwd, $salt);
	$salting_q = "UPDATE Users SET Salt = '" . $salt . "', " .
		"Passwd = '" . $hash . "' WHERE ID = " . $user_id;
	return db_query($salting_q, $dbh);
}

function generate_salt() {
	return md5(uniqid(mt_rand(), true));
}

function salted_hash($passwd, $salt) {
	if (strlen($salt) != 32) {
		trigger_error('Salt does not look like an md5 hash', E_USER_WARNING);
	}
	return md5($salt . $passwd);
}

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
