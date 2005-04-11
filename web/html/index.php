<?
include("index_po.inc");
include("aur.inc");
set_lang();
check_sid();

# Need to do the authentication prior to sending any HTML (including header)
#
$login_error = "";
if (isset($_REQUEST["user"]) || isset($_REQUEST["pass"])) {
	# Attempting to log in
	#
	if (!isset($_REQUEST['user'])) {
		$login_error = __("You must supply a username.");
	}
	if (!isset($_REQUEST['pass'])) {
		$login_error = __("You must supply a password.");
	}
	if (!$login_error) {
		# Try and authenticate the user
		#

		#md5 hash it
		$_REQUEST["pass"] = md5($_REQUEST["pass"]);
		$dbh = db_connect();
		$q = "SELECT ID, Suspended FROM Users ";
		$q.= "WHERE Username = '" . mysql_escape_string($_REQUEST["user"]) . "' ";
		$q.= "AND Passwd = '" . mysql_escape_string($_REQUEST["pass"]) . "'";
		$result = db_query($q, $dbh);
		if (!$result) {
			$login_error = __("Error looking up username, %s.",
						array($_REQUEST["user"]));
		} else {
			$row = mysql_fetch_row($result);
			if (empty($row)) {
				$login_error = __("Incorrect password for username, %s.",
						array($_REQUEST["user"]));
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
				header("Location: /index.php");
			} else {
				$login_error = __("Error trying to generate session id.");
			}
		}
	}
}

# Any cookies have been sent, can now display HTML
#
html_header();

print "<table border='0' cellpadding='0' cellspacing='3' width='90%'>\n";
print "<tr>\n";
print "  <td align='left' valign='top'>";
?>
Welcome to the AUR! If you're a newcomer, you may want to read the <a href="user_docs.html">User Documentation</a> and the <a href="guidelines.html">Guidelines</a>.
<?php
#print __("This is where the intro text will go.");
#print __("For now, it's just a place holder.");
#print __("It's more important to get the login functionality finished.");
#print __("After that, this can be filled in with more meaningful text.");
print "  </td>";
# XXX Is this the proper way to add some spacing between table cells?
#
print "  <td>&nbsp;&nbsp;</td>";
print "  <td align='left' valign='top' nowrap>\n";
if (!isset($_COOKIE["AURSID"])) {
	# the user is not logged in, give them login widgets
	#
	if ($login_error) {
		print "<span class='error'>" . $login_error . "</span><br />\n";
	}
	print "<table border='0' cellpadding='0' cellspacing='0' width='100%'>\n";
	print "<form action='/index.php' method='post'>\n";
	print "<tr>\n";
	print "<td>".__("Username:")."</td>";
	print "<td><input type='text' name='user' size='30' maxlength='64'></td>";
	print "</tr>\n";
	print "<tr>\n";
	print "<td>".__("Password:")."</td>";
	print "<td><input type='password' name='pass' size='30' maxlength='32'></td>";
	print "</tr>\n";
	print "<tr>\n";
	print "<td colspan='2' align='right'>&nbsp;<br />";
	print "<input type='submit' class='button'";
	print " value='".__("Login")."'></td>";
	print "</tr>\n";
	print "</form>\n";
	print "</table>\n";

} else {
	print __("Logged-in as: %h%s%h",
			array("<b>", username_from_sid($_COOKIE["AURSID"]), "</b>"));
}
print "  </td>";
print "</tr>\n";
print "</table>\n";


html_footer("\$Id$");
# vim: ts=2 sw=2 noet ft=php
?>
