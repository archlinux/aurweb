<?
include("aur.inc");         # access AUR common functions
include("pkgfuncs.inc");    # package specific functions
include("search_po.inc");   # use some form of this for i18n support
set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in
html_header();              # print out the HTML header

# enable debugging
#
$DBUG = 0;
if ($DBUG) {
	print "<pre>\n";
	print_r($_REQUEST);
	print "</pre>\n";
}

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
isset($_REQUEST["IDs"]) ? $ids = $_REQUEST["IDs"] : $ids = array();
#isset($_REQUEST["All_IDs"]) ?
#		$all_ids = explode(":", $_REQUEST["All_IDs"]) :
#		$all_ids = array();


# determine what button the visitor clicked
#
if (isset($_REQUEST["do_Flag"])) {
	if (!$atype) {
		print __("You must be logged in before you can flag packages.");
		print "<br />\n";

	} else {

		if (!empty($ids)) {
			$dbh = db_connect();

			# Flag the packages in $ids array
			#
			$first = 1;
			while (list($pid, $v) = each($ids)) {
				if ($first) {
					$first = 0;
					$flag = $pid;
				} else {
					$flag .= ", ".$pid;
				}
			}
			$q = "UPDATE Packages SET OutOfDate = 1 ";
			$q.= "WHERE ID IN (" . $flag . ")";
			db_query($q, $dbh);

			print "<p>\n";
			print __("The selected packages have been flagged out-of-date.");
			print "</p>\n";
		} else {
			print "<p>\n";
			print __("You did not select any packages to flag.");
			print "</p>\n";
		}

		pkgsearch_results_link();
				
	}

} elseif (isset($_REQUEST["do_UnFlag"])) {
	if (!$atype) {
		print __("You must be logged in before you can unflag packages.");
		print "<br />\n";

	} else {

		if (!empty($ids)) {
			$dbh = db_connect();

			# Un-Flag the packages in $ids array
			#
			$first = 1;
			while (list($pid, $v) = each($ids)) {
				if ($first) {
					$first = 0;
					$unflag = $pid;
				} else {
					$unflag .= ", ".$pid;
				}
			}
			$q = "UPDATE Packages SET OutOfDate = 0 ";
			$q.= "WHERE ID IN (" . $unflag . ")";
			db_query($q, $dbh);

			print "<p>\n";
			print __("The selected packages have been unflagged.");
			print "</p>\n";
		} else {
			print "<p>\n";
			print __("You did not select any packages to unflag.");
			print "</p>\n";
		}

		pkgsearch_results_link();
				
	}

} elseif (isset($_REQUEST["do_Disown"])) {
	if (!$atype) {
		print __("You must be logged in before you can disown packages.");
		print "<br />\n";

	} else {
		# Disown the packages in $ids array
		#
		if (!empty($ids)) {
			$dbh = db_connect();

			# Disown the packages in $ids array
			#
			$first = 1;
			while (list($pid, $v) = each($ids)) {
				if ($first) {
					$first = 0;
					$disown = $pid;
				} else {
					$disown .= ", ".$pid;
				}
			}
			# Removed for now since we will have 1 maintainer
			# PJM - 5 April 2005
			#			if ($atype == "Trusted User" || $atype == "Developer") {
			#				$field = "AURMaintainerUID";
			#			} elseif ($atype == "User") {
			#				$field = "MaintainerUID";
			#			} else {
			#				$field = "";
			#			}
			$field = "MaintainerUID";
			if ($field) {
				$q = "UPDATE Packages ";
				$q.= "SET ".$field." = 0 ";
				$q.= "WHERE ID IN (" . $disown . ") ";
				$q.= "AND ".$field." = ".uid_from_sid($_COOKIE["AURSID"]);
				db_query($q, $dbh);
			}

			print "<p>\n";
			print __("The selected packages have been disowned.");
			print "</p>\n";
		} else {
			print "<p>\n";
			print __("You did not select any packages to disown.");
			print "</p>\n";
		}

		pkgsearch_results_link();

	}


} elseif (isset($_REQUEST["do_Delete"])) {
	if (!$atype) {
		print __("You must be logged in before you can disown packages.");
		print "<br />\n";
	} else {
		# Delete the packages in $ids array (but only if they are Unsupported)
		#
		if (!empty($ids)) {
			$dbh = db_connect();

			# Delete the packages in $ids array
			#
			$first = 1;
			while (list($pid, $v) = each($ids)) {
				if ($first) {
					$first = 0;
					$delete = $pid;
				} else {
					$delete .= ", ".$pid;
				}
			}
			#			if ($atype == "Trusted User" || $atype == "Developer") {
			#				$field = "AURMaintainerUID";
			#			} elseif ($atype == "User") {
			#				$field = "MaintainerUID";
			#			} else {
			#				$field = "";
			#				}
			$field = "MaintainerUID";
			if ($field) {
				# Only grab Unsupported packages that "we" own or are not owned at all
				#
				$ids_to_delete = array();
				$q = "SELECT Packages.ID FROM Packages, PackageLocations ";
				$q.= "WHERE Packages.ID IN (" . $delete . ") ";
				$q.= "AND Packages.LocationID = PackageLocations.ID ";
				$q.= "AND PackageLocations.Location = 'unsupported' ";
				$q.= "AND $field IN (0,  " . uid_from_sid($_COOKIE["AURSID"]) . ")";
				$result = db_query($q, $dbh);
				if ($result != Null && mysql_num_rows($result) > 0) {
					while ($row = mysql_fetch_assoc($result)) {
						$ids_to_delete[] = $row['ID'];
					}
				}
				if (!empty($ids_to_delete)) {
					# These are the packages that are safe to delete
					#
				  foreach ($ids_to_delete as $id) {
						# 1) delete from PackageVotes
						$q = "DELETE FROM PackageVotes WHERE PackageID = " . $id;
						$result = db_query($q, $dbh);

						# 2) delete from PackageContents
						$q = "DELETE FROM PackageContents WHERE PackageID = " . $id;
						$result = db_query($q, $dbh);

						# 3) delete from PackageDepends
						$q = "DELETE FROM PackageDepends WHERE PackageID = " . $id;
						$result = db_query($q, $dbh);

						# 4) delete from PackageSources
						$q = "DELETE FROM PackageSources WHERE PackageID = " . $id;
						$result = db_query($q, $dbh);

						# 5) delete from PackageComments
						$q = "DELETE FROM PackageComments WHERE PackageID = " . $id;
						$result = db_query($q, $dbh);

						# 6) delete from Packages
						$q = "DELETE FROM Packages WHERE ID = " . $id;
						$result = db_query($q, $dbh);

						# TODO question: Now that the package as been deleted, does
						#                the unsupported repo need to be regenerated?
					  # ANSWER: No, there is no actual repo for unsupported, so no worries! (PJM)
						# TODO question: What about regenerating the AUR repo? (EJ)

						# Print the success message
						print "<p>\n";
			      print __("The selected packages have been deleted.");
			      print "</p>\n";
					}
				} else {
					print "<p>\n";
					print __("None of the selected packages could be deleted.");
					print "</p>\n";
				} # end if (!empty($ids_to_delete))
			} # end if ($field)
		} else {
			print "<p>\n";
			print __("You did not select any packages to delete.");
			print "</p>\n";
		} # end if (!empty($ids))
		pkgsearch_results_link();
	} # end if (!atype)

} elseif (isset($_REQUEST["do_Adopt"])) {
	if (!$atype) {
		print __("You must be logged in before you can adopt packages.");
		print "<br />\n";

	} else {
		# Adopt the packages in $ids array
		#
		if (!empty($ids)) {
			$dbh = db_connect();

			# Adopt the packages in $ids array
			#
			$first = 1;
			while (list($pid, $v) = each($ids)) {
				if ($first) {
					$first = 0;
					$adopt = $pid;
				} else {
					$adopt .= ", ".$pid;
				}
			}
			#			if ($atype == "Trusted User" || $atype == "Developer") {
			#				$field = "AURMaintainerUID";
			#			} elseif ($atype == "User") {
			#$field = "MaintainerUID";
			#} else {
			#	$field = "";
			#	}
		  $field = "MaintainerUID";
			if ($field) {
				# NOTE: Only "orphaned" packages can be adopted at a particular
				#       user class (TU/Dev or User).
				#
				$q = "UPDATE Packages ";
				$q.= "SET ".$field." = ".uid_from_sid($_COOKIE["AURSID"])." ";
				$q.= "WHERE ID IN (" . $adopt . ") ";
				$q.= "AND ".$field." = 0";
				db_query($q, $dbh);
			}

			print "<p>\n";
			print __("The selected packages have been adopted.");
			print "</p>\n";
		} else {
			print "<p>\n";
			print __("You did not select any packages to adopt.");
			print "</p>\n";
		}

		pkgsearch_results_link();

	}


} elseif (isset($_REQUEST["do_Vote"])) {
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

		pkgsearch_results_link();

	}


} elseif (isset($_REQUEST["do_UnVote"])) {
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

		pkgsearch_results_link();

	}


} elseif (isset($_REQUEST["do_Details"])) {

	if (!isset($_REQUEST["ID"]) || !intval($_REQUEST["ID"])) {
		print __("Error trying to retrieve package details.")."<br />\n";
		
	} else {
		package_details($_REQUEST["ID"]);
	}

	print "<br />\n";
	pkgsearch_results_link();


} else {
	# do_More/do_Less/do_Search/do_MyPackages - just do a search
	#
	pkg_search_page($_COOKIE["AURSID"]);

}

html_footer("\$Id$");
# vim: ts=2 sw=2 noet ft=php
?>
