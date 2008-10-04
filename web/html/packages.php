<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../lang');

include("aur.inc");         # access AUR common functions
include("pkgfuncs.inc");    # package specific functions
include("search_po.inc");   # use some form of this for i18n support
set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in

# set the title to something useful depending on
# what "page" we're on
#
if (isset($_GET['ID'])) {
	$id = pkgname_from_id($_GET['ID']);
	if (!empty($id)) {
		$title = $id;
	}
}	else if (!empty($_GET['K'])) {
	$title = "Search: " . $_GET['K'];
} else {
	$title = __("Packages");
}

html_header($title);

# get login privileges
#
if (isset($_COOKIE["AURSID"])) {
	# Only logged in users can do stuff
	#
	$atype = account_from_sid($_COOKIE["AURSID"]);
} else {
	$atype = "";
}

# grab the list of Package IDs to be operated on
#
isset($_POST["IDs"]) ? $ids = $_POST["IDs"] : $ids = array();

# determine what button the visitor clicked
#
if ($_POST['action'] == "do_Flag" || isset($_POST['do_Flag'])) {
	print "<p>";
	print pkg_flag($atype, $ids, True);
	print "</p>";
} elseif ($_POST['action'] == "do_UnFlag" || isset($_POST['do_UnFlag'])) {
	print "<p>";
	print pkg_flag($atype, $ids, False);
	print "</p>";
} elseif ($_POST['action'] == "do_Disown" || isset($_POST['do_Disown'])) {
	print "<p>";
	print pkg_adopt($atype, $ids, False);
	print "</p>";
} elseif ($_POST['action'] == "do_Delete" || isset($_POST['do_Delete'])) {
	print "<p>";
	print pkg_delete($atype, $ids, False);
	print "</p>";
} elseif ($_POST['action'] == "do_Adopt" || isset($_POST['do_Adopt'])) {
	print "<p>";
	print pkg_adopt($atype, $ids, True);
	print "</p>";
} elseif ($_POST['action'] == "do_Vote" || isset($_POST['do_Vote'])) {
	if (!$atype) {
		print __("You must be logged in before you can vote for packages.");
		print "<br />\n";

	} else {
		# vote on the packages in $ids array.
		#
		if (!empty($ids)) {
			$dbh = db_connect();
			$my_votes = pkgvotes_from_sid($_COOKIE["AURSID"]);
			$uid = uid_from_sid($_COOKIE["AURSID"]);
			# $vote_ids will contain the string of Package.IDs that
			# the visitor hasn't voted for already
			#
			$first = 1;
			while (list($pid, $v) = each($ids)) {
				if (!isset($my_votes[$pid])) {
					# cast a vote for this package
					#
					if ($first) {
						$first = 0;
						$vote_ids = $pid;
						$vote_clauses = "(".$uid.", ".$pid.")";
					} else {
						$vote_ids .= ", ".$pid;
						$vote_clauses .= ", (".$uid.", ".$pid.")";
					}
				}
			}
			# only vote for packages the user hasn't already voted for
			#
			$q = "UPDATE Packages SET NumVotes = NumVotes + 1 ";
			$q.= "WHERE ID IN (".$vote_ids.")";
			db_query($q, $dbh);

			$q = "INSERT INTO PackageVotes (UsersID, PackageID) VALUES ";
			$q.= $vote_clauses;
			db_query($q, $dbh);

			# Update the LastVoted field for this user
			#
			$q = "UPDATE Users SET LastVoted = UNIX_TIMESTAMP() ";
			$q.= "WHERE ID = ".$uid;
			db_query($q, $dbh);

			print "<p>\n";
			print __("Your votes have been cast for the selected packages.");
			print "</p>\n";

		} else {
			print "<p>\n";
			print __("You did not select any packages to vote for.");
			print "</p>\n";
		}
	}


} elseif ($_POST['action'] == "do_UnVote" || isset($_POST['do_UnVote'])) {
	if (!$atype) {
		print __("You must be logged in before you can un-vote for packages.");
		print "<br />\n";

	} else {
		# un-vote on the packages in $ids array.
		#
		if (!empty($ids)) {
			$dbh = db_connect();
			$my_votes = pkgvotes_from_sid($_COOKIE["AURSID"]);
			$uid = uid_from_sid($_COOKIE["AURSID"]);
			# $unvote_ids will contain the string of Package.IDs that
			# the visitor has voted for and wants to unvote.
			#
			$first = 1;
			while (list($pid, $v) = each($ids)) {
				if (isset($my_votes[$pid])) {
					# cast a un-vote for this package
					#
					if ($first) {
						$first = 0;
						$unvote_ids = $pid;
					} else {
						$unvote_ids .= ", ".$pid;
					}
				}
			}
			# only un-vote for packages the user has already voted for
			#
			$q = "UPDATE Packages SET NumVotes = NumVotes - 1 ";
			$q.= "WHERE ID IN (".$unvote_ids.")";
			db_query($q, $dbh);

			$q = "DELETE FROM PackageVotes WHERE UsersID = ".$uid." ";
			$q.= "AND PackageID IN (".$unvote_ids.")";
			db_query($q, $dbh);

			print "<p>\n";
			print __("Your votes have been removed from the selected packages.");
			print "</p>\n";

		} else {
			print "<p>\n";
			print __("You did not select any packages to un-vote for.");
			print "</p>\n";
		}
	}


} elseif (isset($_GET["ID"])) {

	if (!intval($_GET["ID"])) {
		print __("Error trying to retrieve package details.")."<br />\n";
		
	} else {
		package_details($_GET["ID"], $_COOKIE["AURSID"]);
	}

} elseif ($_POST['action'] == "do_Notify" || isset($_POST['do_Notify'])) {
	# I realize that the implementation here seems a bit convoluted, but we want to
	# ensure that everything happens as it should, even if someone called this page
	# without having clicked a button somewhere (naughty naughty). This also leaves
	# room to someday expand and allow to add oneself to multiple lists at once. -SL
	if (!$atype) {
		print __("You must be logged in before you can get notifications on comments.");
		print "<br />\n";
	} else {
		if (!empty($ids)) {
			$dbh = db_connect();
			$uid = uid_from_sid($_COOKIE["AURSID"]);
			# There currently shouldn't be multiple requests here, but the format in which
			# it's sent requires this
			while (list($pid, $v) = each($ids)) {
				$q = "SELECT Name FROM Packages WHERE ID = " . $pid;
				$pkgname = mysql_result(db_query($q, $dbh), 0);

				$q = "SELECT * FROM CommentNotify WHERE UserID = ".$uid;
				$q.= " AND PkgID = ".$pid;

				if (!mysql_num_rows(db_query($q, $dbh))) {
					$q = "INSERT INTO CommentNotify (PkgID, UserID) VALUES (".$pid.', '.$uid.')';
					db_query($q, $dbh);
					print '<p>';
					print __("You have been added to the comment notification list for %s.",
						array("<b>" . $pkgname . "</b>"));
					print '<br /></p>';
				} else {
					$q = "DELETE FROM CommentNotify WHERE PkgID = ".$pid;
					$q.= " AND UserID = ".$uid;
					db_query($q, $dbh);
					print '<p>';
					print __("You have been removed from the comment notification list for %s.",
						array("<b>" . $pkgname . "</b>"));
					print '<br /></p>';
				}
			}
		} else {
			print '<p>';
			print __("Couldn't add to notification list.");
			print '<br /></p>';
		}
	}			
} else {
	# just do a search
	#
	pkg_search_page($_COOKIE["AURSID"]);

}

html_footer(AUR_VERSION);

?>
