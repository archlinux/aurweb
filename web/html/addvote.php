<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../lang');

include("pkgfuncs_po.inc");
include("aur.inc");
set_lang();
check_sid();
html_header();

if (isset($_COOKIE["AURSID"])) {
  $atype = account_from_sid($_COOKIE["AURSID"]);
} else {
  $atype = "";
}

if ($atype == "Trusted User" OR $atype == "Developer") {
	$dbh = db_connect();
	
	if (!empty($_POST['addVote'])) {
		$error = "";
		
		if (!empty($_POST['user'])) {
			$qcheck = "SELECT * FROM Users WHERE Username = '" . mysql_real_escape_string($_POST['user']) . "'";
			$check = mysql_num_rows(db_query($qcheck, $dbh));

			if ($check == 0) {
				$error.= "<div style='color: red; font-weight: bold'>Username does not exist.</div>";
			} else {
				$qcheck = "SELECT * FROM TU_VoteInfo WHERE User = '" . mysql_real_escape_string($_POST['user']) . "'";
				$qcheck.= " AND End > UNIX_TIMESTAMP()";
				$check = mysql_num_rows(db_query($qcheck, $dbh));

				if ($check != 0) {
					$error.= "<div style='color: red; font-weight: bold'>" . htmlentities($_POST['user']) . " already has proposal running for them.</div>";
				}
			}
		}

		if (!empty($_POST['length'])) {
			if (!is_numeric($_POST['length'])) {
				$error.= "<div style='color: red; font-weight: bold'>Length must be a number.</div>";
			} else if ($_POST['length'] < 1) {
				$error.= "<div style='color: red; font-weight: bold'>Length must be at least 1.</div>";
			} else {
				$len = (60*60*24)*$_POST['length'];
			}
		} else {
			$len = 60*60*24*7;
		}

		if (empty($_POST['agenda'])) {
			$error.= "<div style='color: red; font-weight: bold'>Proposal cannot be empty.</div>";
		}
	}

	if (!empty($_POST['addVote']) && empty($error)) {
		$q = "INSERT INTO TU_VoteInfo (Agenda, User, Submitted, End, SubmitterID) VALUES ";
		$q.= "('" . mysql_real_escape_string($_POST['agenda']) . "', ";
		$q.= "'" . mysql_real_escape_string($_POST['user']) . "', ";
		$q.= "UNIX_TIMESTAMP(), UNIX_TIMESTAMP() + " . mysql_real_escape_string($len);
		$q.= ", " . uid_from_sid($_COOKIE["AURSID"]) . ")";

		db_query($q, $dbh);
		print "<p>New proposal submitted.</p>\n";
	} else {
?>
<p>Submit a proposal to vote on.</p>
<?php if (!empty($error)) { print $error . "<br />"; } ?>
<form action='addvote.php' method='post'>
<b>Applicant/TU:</b>
<input type='text' name='user' value='<?php if (!empty($_POST['user'])) { print htmlentities($_POST['user'], ENT_QUOTES); } ?>'>
(empty if not applicable)
<br />
<b>Length in days:</b>
<input type='text' name='length' value='<?php if (!empty($_POST['length'])) { print htmlentities($_POST['length'], ENT_QUOTES); } ?>'>
(defaults to 7 if empty)
<br />
<b>Proposal:</b><br />
<textarea name='agenda' rows='10' cols='50'><?php if (!empty($_POST['agenda'])) { print htmlentities($_POST['agenda']); } ?></textarea><br />
<input type='hidden' name='addVote' value='1'>
<input type='submit' class='button' value='Submit'>
</form>
<br />
<?php
	}
	print "<a href='tu.php'>Back</a>";
} else {
	print "You are not allowed to access this area.\n";
}

html_footer(AUR_VERSION);

?>
