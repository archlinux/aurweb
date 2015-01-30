<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
set_lang();
check_sid();

$title = __("Add Proposal");

html_header($title);

if (isset($_COOKIE["AURSID"])) {
	$uid = uid_from_sid($_COOKIE["AURSID"]);
}

if (has_credential(CRED_TU_ADD_VOTE)) {

	if (!empty($_POST['addVote']) && !check_token()) {
		$error = __("Invalid token for user action.");
	}

	if (!empty($_POST['addVote']) && check_token()) {
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

		if (!empty($_POST['type'])) {
			switch ($_POST['type']) {
			case "add_tu":
				/* Addition of a TU */
				$len = 7 * 24 * 60 * 60;
				$quorum = 0.66;
				break;
			case "remove_tu":
				/* Removal of a TU */
				$len = 7 * 24 * 60 * 60;
				$quorum = 0.75;
				break;
			case "remove_inactive_tu":
				/* Removal of a TU (undeclared inactivity) */
				$len = 5 * 24 * 60 * 60;
				$quorum = 0.66;
				break;
			case "bylaws":
				/* Amendment of Bylaws */
				$len = 7 * 24 * 60 * 60;
				$quorum = 0.75;
				break;
			default:
				$error.=  __("Invalid type.") ;
				break;
			}
		} else {
			$error.=  __("Invalid type.") ;
		}

		if (empty($_POST['agenda'])) {
			$error.= __("Proposal cannot be empty.");
		}
	}

	if (!empty($_POST['addVote']) && empty($error)) {
		add_tu_proposal($_POST['agenda'], $_POST['user'], $len, $quorum, $uid);

		print "<p class=\"pkgoutput\">" . __("New proposal submitted.") . "</p>\n";
	} else {
?>

<?php if (!empty($error)): ?>
	<p style="color: red;" class="pkgoutput"><?= $error ?></p>
<?php endif; ?>

<div class="box">
	<h2><?= __("Submit a proposal to vote on.") ?></h2>

	<form action="<?= get_uri('/addvote/'); ?>" method="post">
		<p>
			<label for="id_user"><?= __("Applicant/TU") ?></label>
			<input type="text" name="user" id="id_user" value="<?php if (!empty($_POST['user'])) { print htmlentities($_POST['user'], ENT_QUOTES); } ?>" />
			<?= __("(empty if not applicable)") ?>
		</p>
		<p>
			<label for="id_type"><?= __("Type") ?></label>
			<select name="type" id="id_type">
				<option value="add_tu"><?= __("Addition of a TU") ?></option>
				<option value="remove_tu"><?= __("Removal of a TU") ?></option>
				<option value="remove_inactive_tu"><?= __("Removal of a TU (undeclared inactivity)") ?></option>
				<option value="bylaws"><?= __("Amendment of Bylaws") ?></option>
			</select>
		</p>
		<p>
		<label for="id_agenda"><?= __("Proposal") ?></label><br />
		<textarea name="agenda" id="id_agenda" rows="15" cols="80"><?php if (!empty($_POST['agenda'])) { print htmlentities($_POST['agenda']); } ?></textarea><br />
		<input type="hidden" name="addVote" value="1" />
		<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
		<input type="submit" class="button" value="<?= __("Submit"); ?>" />
		</p>
	</form>
</div>
<?php
	}
} else {
	print __("You are not allowed to access this area.");
}

html_footer(AURWEB_VERSION);

