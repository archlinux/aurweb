<?
include_once("aur_po.inc");

# TODO do we need to set the domain on cookies?  I seem to remember some
# security concerns about not using domains - but it's not like
# we really care if another site can see what language/SID a user
# is using...
#

# Define global variables
#
$LOGIN_TIMEOUT = 1800;           # number of idle seconds before timeout
$SUPPORTED_LANGS = array(        # what languages we have translations for
	"en" => "English",
	"es" => "Español",
	"de" => "Deutsch",
	"fr" => "Français",
);

# debugging variables
#
$QBUG = 1;                       # toggle query logging to /tmp/aurq.log
$DBUG = 1;                       # use dbug($msg) to log to /tmp/aurd.log


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

# see if the visitor is already logged in
#
function check_sid() {
	global $_COOKIE;
	global $LOGIN_TIMEOUT;

	if (isset($_COOKIE["AURSID"])) {
		$failed = 0;
		# the visitor is logged in, try and update the session
		#
		$dbh = db_connect();
		$q = "SELECT LastUpdateTS, UNIX_TIMESTAMP() FROM Sessions ";
		$q.= "WHERE SessionID = '" . mysql_escape_string($_COOKIE["AURSID"]) . "'";
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
			header("Location: /hacker.php");

		} elseif ($failed == 2) {
			# visitor's session id either doesn't exist, or the timeout
			# was reached and they must login again, send them back to
			# the main page where they can log in again.
			#
			$q = "DELETE FROM Sessions WHERE SessionID = '";
			$q.= mysql_escape_string($_COOKIE["AURSID"]) . "'";
			db_query($q, $dbh);

			setcookie("AURSID", "", time() - (60*60*24*30), "/");
			header("Location: /timeout.php");

		} else {
			# still logged in and haven't reached the timeout, go ahead
			# and update the idle timestamp
			#
			$q = "UPDATE Sessions SET LastUpdateTS = UNIX_TIMESTAMP() ";
			$q.= "WHERE SessionID = '".mysql_escape_string($_COOKIE["AURSID"])."'";
			db_query($q, $dbh);
		}
	}
	return;
}

# verify that an email address looks like it is legitimate
#
function valid_email($addy) {
	return eregi("^[a-z0-9\._-]+@+[a-z0-9\._-]+\.+[a-z]{2,3}$", $addy);
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
	$q = "SELECT Username FROM Users WHERE ID = " . mysql_escape_string($id);
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
	$q.= "AND Sessions.SessionID = '" . mysql_escape_string($sid) . "'";
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
	$q.= "AND Sessions.SessionID = '" . mysql_escape_string($sid) . "'";
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
	$q.= "AND Sessions.SessionID = '" . mysql_escape_string($sid) . "'";
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
	$q.= "AND Sessions.SessionID = '" . mysql_escape_string($sid) . "'";
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
	# NOTE: modify these variables if your MySQL setup is different
	#
	$AUR_db_host = "localhost:/tmp/mysql.sock";
	$AUR_db_name = "AUR";
	$AUR_db_user = "aur";        # XXX use something better when deploying
	$AUR_db_pass = "aur";        # XXX use something better when deploying

	$handle = mysql_pconnect($AUR_db_host, $AUR_db_user, $AUR_db_pass);
	if (!$handle) {
		die("Error connecting to AUR database: " . mysql_error());
	}

	mysql_select_db($AUR_db_name, $handle) or
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
		$fp = fopen("/tmp/aurq.log", "a");
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
	if (isset($_REQUEST['setlang'])) {
		# visitor is requesting a language change
		#
		$LANG = $_REQUEST['setlang'];
		$update_cookie = 1;

	} elseif (isset($_COOKIE['AURLANG'])) {
		# If a cookie is set, use that
		#
		$LANG = $_COOKIE['AURLANG'];

	} elseif (isset($_COOKIE["AURSID"])) {
		$dbh = db_connect();
		$q = "SELECT LangPreference FROM Users, Sessions ";
		$q.= "WHERE Users.ID = Sessions.UsersID ";
		$q.= "AND Sessions.SessionID = '";
		$q.= mysql_escape_string($_COOKIE["AURSID"])."'";
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
	global $LANG;
	print "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
	print "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Strict//EN\"";
	print " \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd\">\n";
	print "<html xmlns=\"http://www.w3.org/1999/xhtml\"";
	print " xml:lang=\"".$LANG."\" lang=\"".$LANG."\">\n";
	print "<head>\n";
	print "<title>AUR (".$LANG.")</title>\n";
	print "<link rel='stylesheet' type='text/css' href='/css/fonts.css'/>\n";
	print "<link rel='stylesheet' type='text/css' href='/css/containers.css'/>\n";
	print "<link rel='shortcut icon' href='/images/favicon.ico'/>\n";
	print "<meta http-equiv=\"Content-Type\"";
	print " content=\"text/html; charset=UTF-8\" />\n";
	print "</head>\n";
	print "<body bgcolor='white'>\n";
	print "<table cellspacing='0' ";
	print "style='background-color: #000; width: 100%;'>\n";
	print "    <tr>\n";
	print "        <td class='preHeader'><span class='preHeader'>";
	print __("%s: An ArchLinux project", array("AUR"));
	print "</span></td>\n";
	print "    </tr>\n";
	print "    <tr>\n";
	print "        <td class='headerFill'>\n";
	print "            <table width='100%'>\n";
	print "            <tr>\n";
	print "                <td class='headerDisplay'><a href='/index.php'>";

	# XXX Can I scale a PNG like this?
	#
	print "<img src='/images/AUR-logo-80.png' width='85' height='45' ";
	print "alt='AUR' border='0' /></a></td>\n";
	print "                <td class='headerDisplay' valign='top' align='right'>";
	print "<span class='preHeader'>ArchLinux User-community Repository</span><br />";

	# XXX CSS help - a:link, a:visited, etc are defined, but I don't want to
	# use the defaults.  Is this the way to override them?
	#
	print "<a href='".$_SERVER["PHP_SELF"]."?setlang=en'><span class='sideBarSmallHeader'>English</span></a> ";
	print "<a href='".$_SERVER["PHP_SELF"]."?setlang=es'><span class='sideBarSmallHeader'>Español</span></a> ";
	print "<a href='".$_SERVER["PHP_SELF"]."?setlang=de'><span class='sideBarSmallHeader'>Deutsch</span></a> ";
	print "<a href='".$_SERVER["PHP_SELF"]."?setlang=fr'><span class='sideBarSmallHeader'>Français</span></a>";
	print "                </td>\n";
	print "            </tr>\n";
	print "            </table>\n";
	print "        </td>\n";
	print "    </tr>\n";

	# Menu items
	#
	print "    <tr>\n";
	print "        <td class='mainLinks' align='center'>";
	print "              <span class='f2'><span class='black'>.:</span>";
	print "            <a href='/index.php'>".__("Home")."</a> ";
	print "              <span class='black'> - </span> ";
	print "            <a href='/account.php'>".__("Accounts")."</a> ";
	print "               <span class='black'> - </span> ";
	print "            <a href='/pkgsearch.php'>".__("Packages")."</a> ";
	if (isset($_COOKIE["AURSID"])) {
		# Only display these items if the visitor is logged in.  This should
		# be a safe check because check_sid() has been called prior to
		# html_header().
		#
		print "               <span class='black'> - </span> ";
		print "            <a href='/pkgvote.php'>".__("Vote")."</a> ";
		print "               <span class='black'> - </span> ";
		print "            <a href='/pkgmgmnt.php'>".__("Manage")."</a> ";
		print "               <span class='black'> - </span> ";
		print "            <a href='/pkgsubmit.php'>".__("Submit")."</a> ";
		print "               <span class='black'> - </span> ";
		print "            <a href='/logout.php'>".__("Logout")."</a> ";
	}
	print "                <span class='black'>:.</span></span>";
	print "        </td>";
	print "    </tr>";
	print "    <tr>\n";
	print "        <td class='contentDisplay'>\n";
	print "        &nbsp;<br />\n";
	print "<!-- Start of main content -->\n\n";

	return;
}


# common footer
#
function html_footer($ver="") {
	print "\n\n<!-- End of main content -->\n";
	print "        <br />\n";
	print "        </td>\n";
	print "    </tr>\n";
	print "</table>\n";
	if ($ver) {
		print "<p>\n";
		print "<table border='0' cellpadding='0' cellspacing='0' width='97%'>\n";
		print "<tr><td align='right'><span class='fix'>".$ver."</span></td></tr>\n";
		print "</table>\n";
		print "</p>\n";
	}
	print "<br />\n";
	print "</body>\n</html>";
	return;
}

# debug logging
#
function dbug($msg) {
	$fp = fopen("/tmp/aurd.log", "a");
	fwrite($fp, $msg . "\n");
	fclose($fp);
	return;
}

# vim: ts=2 sw=2 noet ft=php
?>
