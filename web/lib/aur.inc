<?php
header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-cache, must-revalidate');
header('Expires: Tue, 11 Oct 1988 22:00:00 GMT'); // quite a special day
header('Pragma: no-cache');
include_once("version.inc");
include_once("config.inc");
include_once("aur_po.inc");

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
			header("Location: /timeout.php");

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
	global $LANG;
	echo "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
	echo "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Strict//EN\"";
	echo " \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd\">\n";
	echo "<html xmlns=\"http://www.w3.org/1999/xhtml\"";
	echo " xml:lang=\"".$LANG."\" lang=\"".$LANG."\">\n";
	echo "<head>\n";
	echo "<title>AUR (".$LANG.")</title>\n";
	echo "<link rel='stylesheet' type='text/css' href='/css/fonts.css'/>\n";
	echo "<link rel='stylesheet' type='text/css' href='/css/containers.css'/>\n";
	echo "<link rel='stylesheet' type='text/css' href='/css/arch.css'/>\n";
	echo "<link rel='shortcut icon' href='/images/favicon.ico'/>\n";
	echo "<link rel='alternate' type='application/rss+xml' title='Newest Packages RSS' href='/rss2.php' />\n";
	echo "<meta http-equiv=\"Content-Type\"";
	echo " content=\"text/html; charset=UTF-8\" />\n";
   echo "</head>\n";
   echo "<body bgcolor='white'>\n";
   echo <<<END1
<div id="head_container">
   <div id="title">
      <div id="logo"><a href="/"><img src="/images/logo.png" alt="Arch Logo" /></a></div>
      <div id="titleimg"><a href="/"><img src="/images/title.png" alt="Arch Linux" /></a></div>
   </div>
   <div style="float: right; color: #eeeeee; font-size: small">
   </div>
   <div id="main_nav">
      <ul>
         <li><a href="http://www.archlinux.org/download/">Get Arch</a></li>
         <li class="selected"><a href="http://aur.archlinux.org">AUR</a></li>
         <li><a href="http://bugs.archlinux.org">Bugs</a></li>
         <li><a href="http://wiki.archlinux.org">Wiki</a></li>
         <li><a href="http://bbs.archlinux.org">Forums</a></li>
         <li><a href="http://www.archlinux.org">Home</a></li>
      </ul>
   </div>
   <div id="sub_nav">
      <ul>

END1;
	if ($_COOKIE["AURSID"]) {
      # This is a usability change, so we can go to My Packages page
      # with just one click
      # Added by: dsa <dsandrade@gmail.com>
      echo '        <li><a href="/logout.php">'.__("Logout")."</a></li>\n";
      echo '        <li><a href="/pkgsubmit.php">'.__("Submit")."</a></li>\n";
      echo '        <li><a href="/packages.php?do_MyPackages=1">'.__("My Packages")."</a></li>\n";
	}
   echo '        <li><a href="http://www.archlinux.org/mailman/listinfo/tur-users/">'.__("Discussion")."</a></li>\n";
   echo '        <li><a href="http://bugs.archlinux.org/index.php?tasks=all&project=2">'.__("Bugs")."</a></li>\n";
   echo '        <li><a href="/packages.php">'.__("Packages")."</a></li>\n";
   echo '        <li><a href="/account.php">'.__("Accounts")."</a></li>\n";
   echo '        <li><a href="/index.php">AUR '.__("Home")."</a></li>\n";
   echo "     </ul>\n";
   echo "   </div>\n";
   echo '   <div id="lang_sub">'."\n";
   echo "      <ul>\n";
   echo "         <li><a href='".$_SERVER["PHP_SELF"]."?setlang=ru' title='Русский'>RU</a></li>\n";
   echo "         <li><a href='".$_SERVER["PHP_SELF"]."?setlang=fr' title='Français'>FR</a></li>\n";
   echo "         <li><a href='".$_SERVER["PHP_SELF"]."?setlang=de' title='Deutsch'>DE</a></li>\n";
   echo "         <li><a href='".$_SERVER["PHP_SELF"]."?setlang=es' title='Español'>ES</a></li>\n";
   echo "         <li><a href='".$_SERVER["PHP_SELF"]."?setlang=pt' title='Português'>PT</a></li>\n";
   echo "         <li><a href='".$_SERVER["PHP_SELF"]."?setlang=ca' title='Català'>CA</a></li>\n";
   echo "         <li><a href='".$_SERVER["PHP_SELF"]."?setlang=it' title='Italiano'>IT</a></li>\n";
   echo "         <li><a href='".$_SERVER["PHP_SELF"]."?setlang=pl' title='Polski'>PL</a></li>\n";
   echo "         <li><a href='".$_SERVER["PHP_SELF"]."?setlang=en' title='English'>EN</a></li>\n";
   echo "         <li>Lang: </li>\n";
   echo "      </ul>\n";
   echo "   </div>\n";
   echo "</div>\n";
   echo "<div id=\"maincontent\">\n";
   echo "<!-- Start of main content -->\n\n";
   return;
}


# common footer
#
function html_footer($ver="") {
	print "\n\n<!-- End of main content -->\n";
	print "        <br />\n";
	if ($ver) {
		print "<p>\n";
		print "<table border='0' cellpadding='0' cellspacing='0' width='97%'>\n";
		print "<tr><td align='right'><span class='fix'>".$ver."</span></td></tr>\n";
		print "</table>\n";
		print "</p>\n";
	}
	print "</div>\n";
	print "</body>\n</html>";
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
