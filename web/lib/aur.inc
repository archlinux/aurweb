<?
include_once("aur_po.inc");

# Define global variables
#
$PASS_PHRASE = "Dustyissocool";
$SUPPORTED_LANGS = array(
	"en" => 1, # English
	"es" => 1, # Español
	"de" => 1, # Deutsch
	"fr" => 1, # Français
);

# see if the visitor is already logged in
#
function check_sid() {
	global $_COOKIE;

	if (isset($_COOKIE["AURSID"])) {
		$failed = 0;
		# the visitor is logged in, try and update the session
		#
		$dbh = db_connect();
		$q = "SELECT LastUpdateTS, UNIX_TIMESTAMP() FROM Sessions ";
		$q.= "WHERE SessionID = '" . mysql_escape_string($_COOKIE["AURSID"]) . "'";
		$result = mysql_query($q, $dbh);
		if (!$result) {
			$failed = 1;
		} else {
			if ($row[0] + 10 >= $row[1]) {
				$failed = 1;
			}
		}
		if ($failed) {
			# visitor's session id either doesn't exist, or the timeout
			# was reached and they must login again, send them back to
			# the main page where they can log in again.
			#
			$q = "DELETE FROM Sessions WHERE SessionID = '";
			$q.= mysql_escape_string($_COOKIE["AURSID"]) . "'";
			mysql_query($q, $dbh);

			setcookie("AURSID", "", time() - (60*60*24*30), "/");
			header("Location: /timeout.php");
		}
	}

	return;
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

# obtain the username if given their current SID
#
function username_from_sid($sid="") {
	if (!$sid) {
		return "";
	}
	$dbh = db_connect();
	$q = "SELECT Email ";
	$q.= "FROM Users, Sessions ";
	$q.= "WHERE Users.ID = Sessions.UsersID ";
	$q.= "AND SessionID = '" . mysql_escape_string($sid) . "'";
	$result = mysql_query($q, $dbh);
	if (!$result) {
		return "";
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

	} # TODO query the database if the user is logged in

	if (!$LANG || !array_key_exists($LANG, $SUPPORTED_LANGS)) {
		$LANG = "en"; # default to English
	}

	if ($update_cookie) {
		# TODO do we need to set the domain too?  I seem to remember some
		# security concerns about not using domains - but it's not like
		# we really care if another site can see what language our visitor
		# was using....
		#
		setcookie("AURLANG", $LANG, 0, "/");
	}
	return;
}


# common header
#
function html_header() {
	print "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
	print "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Strict//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd\">\n";
	print "<html xmlns=\"http://www.w3.org/1999/xhtml\" xml:lang=\"en\" lang=\"en\">";
	print "<head>\n";
	print "<title>AUR</title>\n";
	print "<link rel='stylesheet' type='text/css' href='/css/fonts.css'/>\n";
	print "<link rel='stylesheet' type='text/css' href='/css/containers.css'/>\n";
	print "<link rel='shortcut icon' href='/images/favicon.ico'/>\n";
	print "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\" />\n";
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
	print "<img src='/images/AUR-logo-80.png' width='85' height='45' border='0'></a></td>\n";
	print "                <td class='headerDisplay' valign='top' align='right'>";
	print "<span class='preHeader'>ArchLinux User-community Repository</span><br/>";

	# XXX CSS help - a:link, a:visited, etc are defined, but I don't want to
	# use the defaults.  Is this the way to override them?
	#
	print "<a href='/index.php?setlang=en'><span class='sideBarSmallHeader'>English</span></a> ";
	print "<a href='/index.php?setlang=es'><span class='sideBarSmallHeader'>Español</span></a> ";
	print "<a href='/index.php?setlang=de'><span class='sideBarSmallHeader'>Deutsch</span></a> ";
	print "<a href='/index.php?setlang=fr'><span class='sideBarSmallHeader'>Français</span></a>";
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
	print "               <span class='black'> - </span> ";
	print "            <a href='/pkgvote.php'>".__("Vote")."</a> ";
	print "               <span class='black'> - </span> ";
	print "            <a href='/pkgmgmnt.php'>".__("Manage")."</a> ";
	print "               <span class='black'> - </span> ";
	print "            <a href='/pkgsubmit.php'>".__("Submit")."</a> ";
	print "               <span class='black'> - </span> ";
	print "            <a href='/logout.php'>".__("Logout")."</a> ";
	print "                <span class='black'>:.</span></span>";
	print "        </td>";
	print "    </tr>";
	print "    <tr>\n";
	print "        <td class='contentDisplay'>\n";
	print "<!-- Start of main content -->\n\n";

	return;
}


# common footer
#
function html_footer($ver="") {
	print "\n\n<!-- End of main content -->";
	print "        </td>\n";
	print "    </tr>\n";
	print "</table>\n";
	print "<p>\n";
	if ($ver) {
		print "<table border='0' cellpadding='0' cellspacing='0' width='97%'>\n";
		print "<tr><td align='right'><span class='fix'>".$ver."</span></td></tr>\n";
		print "</table>\n";
	}
	print "<\p>\n";
	print "</body>\n</html>";
	return;
}

# vim: ts=2 sw=2 noet ft=php
?>
