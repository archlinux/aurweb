<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
set_lang();
check_sid();

$title = __("Add Proposal");

html_header($title);

if (isset($_COOKIE["AURSID"])) {
  $atype = account_from_sid($_COOKIE["AURSID"]);
  $uid = uid_from_sid($_COOKIE["AURSID"]);
} else {
  $atype = "";
}

if ($atype == "Trusted User" || $atype == "Developer") {

	if (!empty($_POST['addVote'])) {
		$error = "";

		if (!empty($_POST['user'])) {
			if (!valid_user($_POST['user'])) {
				$error.= __("Username does not exist.");
			} else {

				if (open_user_proposals($_POST['user'])) {
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
		add_tu_proposal($_POST['agenda'], $_POST['user'], $len, $uid);

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

