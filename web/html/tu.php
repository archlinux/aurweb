<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
set_lang();
check_sid();

$title = __("Trusted User");

html_header($title);

# Default votes per page
$pp = 10;
$prev_Len = 75;

if (has_credential(CRED_TU_LIST_VOTES)) {

	if (isset($_GET['id'])) {
		if (is_numeric($_GET['id'])) {
			$row = vote_details($_GET['id']);

			if (empty($row)) {
				print __("Could not retrieve proposal details.");
			} else {
				$isrunning = $row['End'] > time() ? 1 : 0;

				# List voters of a proposal.
				$whovoted = voter_list($row['ID']);

				$canvote = 1;
				$hasvoted = 0;
				$errorvote = "";
				if ($isrunning == 0) {
					$canvote = 0;
					$errorvote = __("Voting is closed for this proposal.");
				} else if (!has_credential(CRED_TU_VOTE)) {
					$canvote = 0;
					$errorvote = __("Only Trusted Users are allowed to vote.");
				} else if ($row['User'] == username_from_sid($_COOKIE["AURSID"])) {
					$canvote = 0;
					$errorvote = __("You cannot vote in an proposal about you.");
				}
				if (tu_voted($row['ID'], uid_from_sid($_COOKIE["AURSID"]))) {
					$canvote = 0;
					$hasvoted = 1;
					if ($isrunning) {
						$errorvote = __("You've already voted for this proposal.");
					}
				}

				if ($canvote == 1) {
					if (isset($_POST['doVote']) && check_token()) {
						if (isset($_POST['voteYes'])) {
							$myvote = "Yes";
						} else if (isset($_POST['voteNo'])) {
							$myvote = "No";
						} else if (isset($_POST['voteAbstain'])) {
							$myvote = "Abstain";
						}

						cast_proposal_vote($row['ID'], uid_from_sid($_COOKIE["AURSID"]), $myvote, $row[$myvote] + 1);

						# Can't vote anymore
						#
						$canvote = 0;
						$errorvote = __("You've already voted for this proposal.");

						# Update if they voted
						if (tu_voted($row['ID'], uid_from_sid($_COOKIE["AURSID"]))) {
							$hasvoted = 1;
						}
						$row = vote_details($_GET['id']);
					}
				}
				include("tu_details.php");
			}
		} else {
			print __("Vote ID not valid.");
		}

	} else {
		$limit = $pp;
		if (isset($_GET['off']))
			$offset = $_GET['off'];

		if (isset($_GET['by']))
			$by = $_GET['by'];
		else
			$by = 'desc';

		if (!empty($offset) && is_numeric($offset)) {
			if ($offset >= 1) {
				$off = $offset;
			} else {
				$off = 0;
			}
		} else {
			$off = 0;
		}

		$order = ($by == 'asc') ? 'ASC' : 'DESC';
		$lim = ($limit > 0) ? " LIMIT $limit OFFSET $off" : "";
		$by_next = ($by == 'desc') ? 'asc' : 'desc';

		$result = current_proposal_list($order);
		$type = __("Current Votes");
		$nextresult = 0;
		include("tu_list.php");

		$result = past_proposal_list($order, $lim);
		$type = __("Past Votes");
		$nextresult = proposal_count();
		include("tu_list.php");

		$result = last_votes_list();
		include("tu_last_votes_list.php");
	}
}
else {
	header('Location: /');
}

html_footer(AURWEB_VERSION);

