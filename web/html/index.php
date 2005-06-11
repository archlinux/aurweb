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
print "<p>".__("Welcome to the AUR! If you're a newcomer, you may want to read the %hGuidelines%h.", array('<a href="guidelines.html">', '</a>'))."</p>";
print "<p>".__("If you have feedback about the AUR, please leave it in %hFlyspray%h.", array('<a href="http://bugs.archlinux.org/index.php?tasks=all&amp;project=2">', '</a>'))."</p>";
print "<p>".__("Email discussion about the AUR takes place on the %sTUR Users List%s.", array('<a href="http://www.archlinux.org/mailman/listinfo/tur-users">', '</a>'));
print "<p>".__("Though we can't vouch for their contents, we provide a %hlist of user repositories%h for your convenience.", array('<a href="http://wiki2.archlinux.org/index.php/Unofficial%20Repositories">', '</a>'))."</p>";

print "<br>\n";

#Hey, how about listing the newest pacakges? :D
$q = "SELECT * FROM Packages ";
$q.= "WHERE DummyPkg != 1 ";
$q.= "ORDER BY SubmittedTS DESC ";
$q.= "LIMIT 0 , 10";
$result = db_query($q,$dbh);
print '<table cellspacing="2" class="boxSoft"><tr><td class="boxSoftTitle" align="right"><span class="f3">'.__("Recent Updates").'</span> </td> </tr><tr><td class="boxSoft"><table style="width: 100%" cellspacing=0 cellpadding=0>'."\n";
while ($row = mysql_fetch_assoc($result)) {
	print '<tr><td><span class="f4"><span class="blue">- <a href="/packages.php?do_Details=1&ID='.intval($row["ID"]).'">';
	print $row["Name"]." ".$row["Version"]."</a></span></span>";
	#print '<td align="right"><span class="f4">'.intval($row["ModifiedTS"]).'</span></td>';
	print '</tr>'."\n";
}
print '</table></td></tr></table>';

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


html_footer("<b>Version 1.1</b> \$Id$");
# vim: ts=2 sw=2 noet ft=php
?>
