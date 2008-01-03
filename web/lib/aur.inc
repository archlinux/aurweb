<?php
set_include_path(get_include_path() . PATH_SEPARATOR . '../template');
header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-cache, must-revalidate');
header('Expires: Tue, 11 Oct 1988 22:00:00 GMT'); // quite a special day
header('Pragma: no-cache');
include_once("version.inc");
include_once("config.inc");
include_once("aur_po.inc");
include_once("index_po.inc");

# TODO do we need to set the domain on cookies?  I seem to remember some
# security concerns about not using domains - but it's not like
# we really care if another site can see what language/SID a user
# is using...
#



# return an array of info for each Trusted user
#
function getTrustedUsers() {
	$tus = array();
	$dbh = db_connect();
	$q = "SELECT * FROM Users WHERE AccountTypeID = 2 ";
	$q.= "ORDER BY Username ASC";
	$result = db_query($q, $dbh);
	if ($result) {
		while ($row = mysql_fetch_assoc($result)) {
			$tus[$row["ID"]] = $row;
		}
	}
	return $tus;
}


# return an array of info for each Developer
#
function getDevelopers() {
	$devs = array();
	$dbh = db_connect();
	$q = "SELECT * FROM Users WHERE AccountTypeID = 3 ";
	$q.= "ORDER BY Username ASC";
	$result = db_query($q, $dbh);
	if ($result) {
		while ($row = mysql_fetch_assoc($result)) {
			$devs[$row["ID"]] = $row;
		}
	}
	return $devs;
}

# return an array of info for each user
function getUsers() {
	$users = array();
	$dbh = db_connect();
	$q = "SELECT * FROM Users ORDER BY Username ASC";
	$result = db_query($q, $dbh);
	if ($result) {
		while ($row = mysql_fetch_assoc($result)) {
			$users[$row["ID"]] = $row;
		}
	}
	return $users;
}

# see if the visitor is already logged in
#
function check_sid() {
	global $_COOKIE;
	global $LOGIN_TIMEOUT;

	if ($_COOKIE["AURSID"]) {
		$failed = 0;
		# the visitor is logged in, try and update the session
		#
		$dbh = db_connect();
		$q = "SELECT LastUpdateTS, UNIX_TIMESTAMP() FROM Sessions ";
		$q.= "WHERE SessionID = '" . mysql_real_escape_string($_COOKIE["AURSID"]) . "'";
		$result = db_query($q, $dbh);
		if (!$result) {
			# Invalid SessionID - hacker alert!
			#
			$failed = 1;
		} else {
			$row = mysql_fetch_row($result);
			if ($row[0] + $LOGIN_TIMEOUT <= $row[1]) {
				dbug("login timeout reached");
				$failed = 2;
			}
		}
		if ($failed == 1) {
			# clear out the hacker's cookie, and send them to a naughty page
			#
			setcookie("AURSID", "", time() - (60*60*24*30), "/");
			# I think it's probably safe to do the same as below with this
			# but not really vital at this point
			header("Location: /hacker.php");

		} elseif ($failed == 2) {
			# visitor's session id either doesn't exist, or the timeout
			# was reached and they must login again, send them back to
			# the main page where they can log in again.
			#
			$q = "DELETE FROM Sessions WHERE SessionID = '";
			$q.= mysql_real_escape_string($_COOKIE["AURSID"]) . "'";
			db_query($q, $dbh);

			setcookie("AURSID", "", time() - (60*60*24*30), "/");
			unset($_COOKIE['AURSID']);
		} else {
			# still logged in and haven't reached the timeout, go ahead
			# and update the idle timestamp
			#
			$q = "UPDATE Sessions SET LastUpdateTS = UNIX_TIMESTAMP() ";
			$q.= "WHERE SessionID = '".mysql_real_escape_string($_COOKIE["AURSID"])."'";
			db_query($q, $dbh);
		}
	}
	return;
}

# verify that an email address looks like it is legitimate
#
function valid_email($addy) {
	return eregi("^[a-z0-9\._-]+@+[a-z0-9\._-]+\.+[a-z]{2,4}$", $addy);
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
	mt_srand(make_seed());
	$ts = time();
	$pid = getmypid();

	$rand_num = mt_rand();
	mt_srand(make_seed());
	$rand_str = substr(md5(mt_rand()),2, 20);

	$id = $rand_str . strtolower(md5($ts.$pid)) . $rand_num;
	return strtoupper(md5($id));
}


# obtain the username if given their Users.ID
#
function username_from_id($id="") {
	if (!$id) {
		return "";
	}
	$dbh = db_connect();
	$q = "SELECT Username FROM Users WHERE ID = " . mysql_real_escape_string($id);
	$result = db_query($q, $dbh);
	if (!$result) {
		return "None";
	}
	$row = mysql_fetch_row($result);

	return $row[0];
}


# obtain the username if given their current SID
#
function username_from_sid($sid="") {
	if (!$sid) {
		return "";
	}
	$dbh = db_connect();
	$q = "SELECT Username ";
	$q.= "FROM Users, Sessions ";
	$q.= "WHERE Users.ID = Sessions.UsersID ";
	$q.= "AND Sessions.SessionID = '" . mysql_real_escape_string($sid) . "'";
	$result = db_query($q, $dbh);
	if (!$result) {
		return "";
	}
	$row = mysql_fetch_row($result);

	return $row[0];
}

# obtain the email address if given their current SID
#
function email_from_sid($sid="") {
	if (!$sid) {
		return "";
	}
	$dbh = db_connect();
	$q = "SELECT Email ";
	$q.= "FROM Users, Sessions ";
	$q.= "WHERE Users.ID = Sessions.UsersID ";
	$q.= "AND Sessions.SessionID = '" . mysql_real_escape_string($sid) . "'";
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
function account_from_sid($sid="") {
	if (!$sid) {
		return "";
	}
	$dbh = db_connect();
	$q = "SELECT AccountType ";
	$q.= "FROM Users, AccountTypes, Sessions ";
	$q.= "WHERE Users.ID = Sessions.UsersID ";
	$q.= "AND AccountTypes.ID = Users.AccountTypeID ";
	$q.= "AND Sessions.SessionID = '" . mysql_real_escape_string($sid) . "'";
	$result = db_query($q, $dbh);
	if (!$result) {
		return "";
	}
	$row = mysql_fetch_row($result);

	return $row[0];
}

# obtain the Users.ID if given their current SID
#
function uid_from_sid($sid="") {
	if (!$sid) {
		return "";
	}
	$dbh = db_connect();
	$q = "SELECT Users.ID ";
	$q.= "FROM Users, Sessions ";
	$q.= "WHERE Users.ID = Sessions.UsersID ";
	$q.= "AND Sessions.SessionID = '" . mysql_real_escape_string($sid) . "'";
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

	$handle = mysql_pconnect(AUR_db_host, AUR_db_user, AUR_db_pass);
	if (!$handle) {
		die("Error connecting to AUR database: " . mysql_error());
	}

	mysql_select_db(AUR_db_name, $handle) or
		die("Error selecting AUR database: " . mysql_error());

	return $handle;
}

# wrapper function around db_query in case we want to put
# query logging/debuggin in.
#
function db_query($query="", $db_handle="") {
	global $QBUG;
	if (!$query) {
		return FALSE;
	}
	if (!$db_handle) {
		$db_handle = db_connect();
	}
	if ($QBUG) {
		$fp = fopen(AURQ_LOG, "a");
		fwrite($fp, $query . "\n");
		fclose($fp);
	}
	$result = @mysql_query($query, $db_handle);
	return $result;
}

# set up the visitor's language
#
function set_lang() {
	global $_REQUEST;
	global $_COOKIE;
	global $LANG;
	global $SUPPORTED_LANGS;

	$update_cookie = 0;
	if ($_REQUEST['setlang']) {
		# visitor is requesting a language change
		#
		$LANG = $_REQUEST['setlang'];
		$update_cookie = 1;

	} elseif ($_COOKIE['AURLANG']) {
		# If a cookie is set, use that
		#
		$LANG = $_COOKIE['AURLANG'];

	} elseif ($_COOKIE["AURSID"]) {
		$dbh = db_connect();
		$q = "SELECT LangPreference FROM Users, Sessions ";
		$q.= "WHERE Users.ID = Sessions.UsersID ";
		$q.= "AND Sessions.SessionID = '";
		$q.= mysql_real_escape_string($_COOKIE["AURSID"])."'";
		$result = db_query($q, $dbh);
		if (!$result) {
			$LANG = "en";
		} else {
			$row = mysql_fetch_array($result);
			$LANG = $row[0];
		}
		$update_cookie = 1;
	} else {
		$LANG = "en";
	}

	if (!array_key_exists($LANG, $SUPPORTED_LANGS)) {
		$LANG = "en"; # default to English
	}

	if ($update_cookie) {
		setcookie("AURLANG", $LANG, 0, "/");
	}
	return;
}


# common header
#
function html_header() {
	global $_SERVER;
	global $_COOKIE;
	global $_POST;
	global $LANG;
	global $SUPPORTED_LANGS;

	$login_error = "";
	if (isset($_POST["user"]) || isset($_POST["pass"])) {
		# Attempting to log in
		#
		if (!isset($_POST["user"])) {
			$login_error = __("You must supply a username.");
		}
		if (!isset($_POST["pass"])) {
			$login_error = __("You must supply a password.");
		}
		if (!$login_error) {
			# Try and authenticate the user
			#

			#md5 hash it
			$_POST["pass"] = md5($_POST["pass"]);
			$dbh = db_connect();
			$q = "SELECT ID, Suspended FROM Users ";
			$q.= "WHERE Username = '" . mysql_real_escape_string($_POST["user"]) . "' ";
			$q.= "AND Passwd = '" . mysql_real_escape_string($_POST["pass"]) . "'";
			$result = db_query($q, $dbh);
			if (!$result) {
				$login_error = __("Error looking up username, %s.",
							array(htmlspecialchars($_POST["user"])));
			} else {
				$row = mysql_fetch_row($result);
				if (empty($row)) {
					$login_error = __("Incorrect password for username, %s.",
							array(htmlspecialchars($_POST["user"])));
				} elseif ($row[1]) {
					$login_error = __("Your account has been suspended.");
				}
			}

			if (!$login_error) {
				# Account looks good.  Generate a SID and store it.
				#
				$logged_in = 0;
				$num_tries = 0;
				while (!$logged_in && $num_tries < 5) {
					$new_sid = new_sid();
					$q = "INSERT INTO Sessions (UsersID, SessionID, LastUpdateTS) ";
					$q.="VALUES (". $row[0]. ", '" . $new_sid . "', UNIX_TIMESTAMP())";
					$result = db_query($q, $dbh);
					# Query will fail if $new_sid is not unique
					#
					if ($result) {
						$logged_in = 1;
						break;
					}
					$num_tries++;
				}
				if ($logged_in) {
					# set our SID cookie
					#
					setcookie("AURSID", $new_sid, 0, "/");
					$_COOKIE['AURSID'] = $new_sid;
				} else {
					$login_error = __("Error trying to generate session id.");
				}
			}
		}
	}

	include('header.php');
	return;
}


# common footer
#
function html_footer($ver="") {
	include('footer.php');
	return;
}

# debug logging
#
function dbug($msg) {
	$fp = fopen(AURD_LOG, "a");
	fwrite($fp, $msg . "\n");
	fclose($fp);
	return;
}

# check to see if the user can overwrite an existing package
#
function can_overwrite_pkg($name="", $sid="") {
	if (!$name || !$sid) {return 0;}
	$dbh = db_connect();
	$q = "SELECT SubmitterUID, MaintainerUID, AURMaintainerUID ";
	$q.= "FROM Packages WHERE Name = '".mysql_real_escape_string($name)."'";
	$result = db_query($q, $dbh);
	if (!$result) {return 0;}
	$row = mysql_fetch_row($result);
	$my_uid = uid_from_sid($sid);

	# user is a dev and maintains the package
	#
	if ($my_uid == $row[2]) {return 1;}

	# user is a TU and there is no dev
	#
	if (!$row[2] && $my_uid == $row[1]) {return 1;}

	# user is a user and there is no TU or dev
	#
	if (!$row[2] && !$row[1] && $my_uid == $row[0]) {return 1;}
	return 0;
}

# convert an ini_get number to a real integer - stupid PHP!
#
function initeger($inival="0", $isbytes=1) {
	$last_char = strtolower(substr($inival, -1));
	if ($isbytes) {
		switch ($last_char) {
			case 't': $multiplier = 1024 * 1024 * 1024; break;
			case 'm': $multiplier = 1024 * 1024; break;
			case 'k': $multiplier = 1024; break;
			default:  $multiplier = 1; break;
		}
	} else {
		switch ($last_char) {
			case 't': $multiplier = 1000 * 1000 * 1000; break;
			case 'm': $multiplier = 1000 * 1000; break;
			case 'k': $multiplier = 1000; break;
			default:  $multiplier = 1; break;
		}
	}

	return intval($inival) * $multiplier;
}

# recursive delete directory
#
function rm_rf($dirname="") {
	$d = dir($dirname);
	while ($f = $d->read()) {
		if ($f != "." && $f != "..") {
			if (is_dir($dirname."/".$f)) {
				rm_rf($dirname."/".$f);
			}
			if (is_file($dirname."/".$f) || is_link($dirname."/".$f)) {
				unlink($dirname."/".$f);
			}
		}
	}
	$d->close();
	rmdir($dirname);
	return;
}

# obtain the uid given a Users.Username
#
function uid_from_username($username="")
{
	if (!$username) {
		return "";
	}
	$dbh = db_connect();
	$q = "SELECT ID FROM Users WHERE Username = '".mysql_real_escape_string($username)
				."'";
	$result = db_query($q, $dbh);
	if (!$result) {
		return "None";
	}
	$row = mysql_fetch_row($result);
	
	return $row[0];
}

# vim: ts=2 sw=2 noet ft=php
?>
