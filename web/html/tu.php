<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include("aur.inc");
set_lang();
check_sid();
html_header();

# Default votes per page
$pp = 10;
$prev_Len = 75;

$atype = "";
if (isset($_COOKIE["AURSID"])) {
  $atype = account_from_sid($_COOKIE["AURSID"]);
}

if ($atype == "Trusted User" OR $atype == "Developer") {

	if (isset($_GET['id'])) {
		if (is_numeric($_GET['id'])) {

			$q = "SELECT * FROM TU_VoteInfo ";
			$q.= "WHERE ID = " . $_GET['id'];

			$dbh = db_connect();
			$results = db_query($q, $dbh);
			$row = mysql_fetch_assoc($results);
			
			if (empty($row)) {
				print __("Could not retrieve proposal details.");
			} else {
				$isrunning = $row['End'] > time() ? 1 : 0;
				
				$qvoted = "SELECT * FROM TU_Votes WHERE ";
				$qvoted.= "VoteID = " . $row['ID'] . " AND ";
				$qvoted.= "UserID = " . uid_from_sid($_COOKIE["AURSID"]);
				$hasvoted = mysql_num_rows(db_query($qvoted, $dbh));

				$canvote = 1;
				$errorvote = "";
				if ($isrunning == 0) {
					$canvote = 0;
					$errorvote = __("Voting is closed for this proposal.");
				} else if ($row['User'] == username_from_sid($_COOKIE["AURSID"])) {
					$canvote = 0;
					$errorvote = __("You cannot vote in an proposal about you.");
				} else if ($hasvoted != 0) {
					$canvote = 0;
					$errorvote = __("You've already voted in this proposal.");
				}

				if ($canvote == 1) {
					if (isset($_POST['doVote'])) {
						if (isset($_POST['voteYes'])) {
							$myvote = __("Yes");
						} else if (isset($_POST['voteNo'])) {
							$myvote = __("No");
						} else if (isset($_POST['voteAbstain'])) {
							$myvote = __("Abstain");
						}

						$qvote = "UPDATE TU_VoteInfo SET " . $myvote . " = " . ($row[$myvote] + 1) . " WHERE ID = " . $row['ID'];
						db_query($qvote, $dbh);
						$qvote = "INSERT INTO TU_Votes (VoteID, UserID) VALUES (" . $row['ID'] . ", " . uid_from_sid($_COOKIE["AURSID"]) . ")";
						db_query($qvote, $dbh);

						# Can't vote anymore
						#
						$canvote = 0;
						$errorvote = __("You've already voted for this proposal.");
						# Update if they voted
						$hasvoted = mysql_num_rows(db_query($qvoted, $dbh));
						
						$results = db_query($q, $dbh);
						$row = mysql_fetch_assoc($results);
					}
				}
				include("tu_details.php");
			}
		} else {
			print __("Vote ID not valid.");
		}

	} else {
		$dbh = db_connect();
		
		$limit = $pp;
		if (isset($_GET['off']))
			$offset = $_GET['off'];

		if (isset($_GET['by']))
			$by = $_GET['by'];
		else
			$by = 'up';

		if (!empty($offset) AND is_numeric($offset)) {
			if ($offset >= 1) {
				$off = $offset;
			} else {
				$off = 0;
			}
		} else {
			$off = 0;
		}

		$order = ($by == 'down') ? 'DESC' : 'ASC';
		$lim = ($limit > 0) ? " LIMIT " . $off . ", " . $limit : "";
		$by_next = ($by == "down") ? "up" : "down";

		$q = "SELECT * FROM TU_VoteInfo WHERE End > " . time() . " ORDER BY Submitted " . $order;
		$result = db_query($q, $dbh);

		$type = __("Current Votes");
		include("tu_list.php");
?>

<center>
	<a href='addvote.php'><?php print __("Add") ?></a>
</center><br />

<?php
		$q = "SELECT * FROM TU_VoteInfo ORDER BY Submitted " . $order . $lim;
		$result = db_query($q, $dbh);

		$type = __("All Votes");
		include("tu_list.php");

		$qnext = "SELECT ID FROM TU_VoteInfo";
		$nextresult = db_query($qnext, $dbh);
?>
<table style='width: 90%'>
	<?php if (mysql_num_rows($result)) { $by = htmlentities($by, ENT_QUOTES); ?>
	<tr>
	<td align='left'>
	<?php if ($off != 0) { $back = (($off - $limit) <= 0) ? 0 : $off - $limit; ?>
	<a href='tu.php?off=<?php print $back ?>&amp;by=<?php print $by ?>'><?php print __("Back") ?></a>
	<?php } ?>
	</td>
	<td align='right'>
	<?php if (($off + $limit) < mysql_num_rows($nextresult)) { $forw = $off + $limit; ?>
	<a href='tu.php?off=<?php print $forw ?>&amp;by=<?php print $by ?>'><?php print __("Next") ?></a>
	<?php } ?>
	</td>
	</tr>
	<?php } ?>
</table>
<?php
	}
}
else {
	header('Location: index.php');
}

html_footer(AUR_VERSION);

