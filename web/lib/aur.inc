<?
include_once("aur_po.inc");

# Define global variables
#


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


# common header
#
function html_header() {
	print "<html>\n";
	print "<head>\n";
	print "<title>AUR</title>\n";
	print "<link rel='stylesheet' type='text/css' href='/css/fonts.css'/>\n";
	print "<link rel='stylesheet' type='text/css' href='/css/containers.css'/>\n";
	print "<link rel='shortcut icon' href='/images/favicon.ico'/>\n";
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
	print "                <td class='headerDisplay'><a href='";
	print $_SERVER['PHP_SELF']."'>";
	print "<img src='/images/AUR-logo-80.png' border='0'></a></td>\n";
	print "                <td class='headerDisplay' valign='top' align='right'>";
	print "<span class='fix'>ArchLinux User-community Repository</span></td>\n";
	print "            </tr>\n";
	print "            </table>\n";
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
		print "<table border='0' cellpadding='0' cellspacing='0' width='100%'>\n";
		print "<tr><td align='right'><span class='fix'>".$ver."</span></td></tr>\n";
		print "</table>\n";
	}
	print "</body>\n</html>";
	return;
}

# vim: ts=2 sw=2 noet ft=php
?>
