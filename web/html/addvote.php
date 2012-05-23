<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
set_lang();
check_sid();

$title = __("Add Proposal");

html_header($title);

if (isset($_COOKIE["AURSID"])) {
  $atype = account_from_sid($_COOKIE["AURSID"]);
} else {
  $atype = "";
}

if ($atype == "Trusted User" || $atype == "Developer") {
	$dbh = db_connect();

	if (!empty($_POST['addVote'])) {
		$error = "";

		if (!empty($_POST['user'])) {
			$qcheck = "SELECT * FROM Users WHERE Username = '" . db_escape_string($_POST['user']) . "'";
			$result = db_query($qcheck, $dbh);
			if ($result) {
				$check = mysql_num_rows($result);
			}
			else {
				$check = 0;
			}

			if ($check == 0) {
				$error.= __("Username does not exist.");
			} else {
				$qcheck = "SELECT * FROM TU_VoteInfo WHERE User = '" . db_escape_string($_POST['user']) . "'";
				$qcheck.= " AND End > UNIX_TIMESTAMP()";
				$result = db_query($qcheck, $dbh);
				if ($result) {
					$check = mysql_num_rows($result);
				}
				else {
					$check = 0;
				}

				if ($check != 0) {
					$error.= __("%s already has proposal running for them.", htmlentities($_POST['user']));
				}
			}
		}

		if (!empty($_POST['length'])) {
			if (!is_numeric($_POST['length'])) {
				$error.=  __("Length must be a number.") ;
			} else if ($_POST['length'] < 1) {
				$error.= __("Length must be at least 1.");
			} else {
				$len = (60*60*24)*$_POST['length'];
			}
		} else {
			$len = 60*60*24*7;
		}

		if (empty($_POST['agenda'])) {
			$error.= __("Proposal cannot be empty.");
		}
	}

	if (!empty($_POST['addVote']) && empty($error)) {
		$q = "INSERT INTO TU_VoteInfo (Agenda, User, Submitted, End, SubmitterID) VALUES ";
		$q.= "('" . db_escape_string($_POST['agenda']) . "', ";
		$q.= "'" . db_escape_string($_POST['user']) . "', ";
		$q.= "UNIX_TIMESTAMP(), UNIX_TIMESTAMP() + " . db_escape_string($len);
		$q.= ", " . uid_from_sid($_COOKIE["AURSID"]) . ")";

		db_query($q, $dbh);
		print "<p class=\"pkgoutput\">" . __("New proposal submitted.") . "</p>\n";
	} else {
?>

<?php if (!empty($error)): ?>
	<p style="color: red;" class="pkgoutput"><?php print $error ?></p>
<?php endif; ?>

<div class="box">
	<h2><?php print __("Submit a proposal to vote on.") ?></h2>

	<form action="addvote.php" method="post">
		<p>
			<b><?php print __("Applicant/TU") ?></b>
			<input type="text" name="user" value="<?php if (!empty($_POST['user'])) { print htmlentities($_POST['user'], ENT_QUOTES); } ?>" />
			<?php print __("(empty if not applicable)") ?>
		</p>
		<p>
			<b><?php print __("Length in days") ?></b>
			<input type="text" name="length" value="<?php if (!empty($_POST['length'])) { print htmlentities($_POST['length'], ENT_QUOTES); } ?>" />
			<?php print __("(defaults to 7 if empty)") ?>
		</p>
		<p>
		<b><?php print __("Proposal") ?></b><br />
		<textarea name="agenda" rows="15" cols="80"><?php if (!empty($_POST['agenda'])) { print htmlentities($_POST['agenda']); } ?></textarea><br />
		<input type="hidden" name="addVote" value="1" />
		<input type="submit" class="button" value="<?php print __("Submit"); ?>" />
		</p>
	</form>
</div>
<?php
	}
} else {
	print __("You are not allowed to access this area.");
}

html_footer(AUR_VERSION);

