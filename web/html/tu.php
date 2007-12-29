<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../lang');

include("pkgfuncs_po.inc");
include("aur.inc");
set_lang();
check_sid();
html_header();

# get login privileges
#
if (isset($_COOKIE["AURSID"])) {
  # Only logged in users can do stuff
  #
  $atype = account_from_sid($_COOKIE["AURSID"]);
} else {
  $atype = "";
}

if ($atype == "Trusted User" OR $atype == "Developer") {
	# Show the TU interface
	# 

	# Temp value for results per page
	$pp = 5;

	if (isset($_REQUEST['id'])) {
		# Show application details
		# depending on action and time frame will show either
		# sponsor button, comments and vote buttons
		#

		if (intval($_REQUEST['id'])) {

			$q = "SELECT * FROM TU_VoteInfo ";
			$q.= "WHERE ID = " . $_REQUEST['id'];

			$dbh = db_connect();
			$results = db_query($q, $dbh);
			$row = mysql_fetch_assoc($results);
			
			if (empty($row)) {
				print "Could not retrieve proposal details.\n";
			} else {
				# Print out application details, thanks again AUR
				#

				$isrunning = $row['End'] > time() ? 1 : 0;
				
				$qvoted = "SELECT * FROM TU_Votes WHERE ";
				$qvoted.= "VoteID = " . $row['ID'] . " AND ";
				$qvoted.= "UserID = " . uid_from_sid($_COOKIE["AURSID"]);
				$hasvoted = mysql_num_rows(db_query($qvoted, $dbh));

				# Can this person vote?
				#
				$canvote = 1; // we assume they can
				$errorvote = ""; // error message to give
				if ($isrunning == 0) {
					$canvote = 0;
					$errorvote = "Voting is closed for this proposal.";
				} else if ($row['User'] == username_from_sid($_COOKIE["AURSID"])) {
					$canvote = 0;
					$errorvote = "You cannot vote in an proposal regarding you.";
				} else if ($hasvoted != 0) {
					$canvote = 0;
					$errorvote = "You've already voted in this proposal.";
				}

				# have to put this here so results are correct immediately after voting	
				if ($canvote == 1) {
					if (isset($_POST['doVote'])) {
						if (isset($_POST['voteYes'])) {
							$myvote = "Yes";
						} else if (isset($_POST['voteNo'])) {
							$myvote = "No";
						} else if (isset($_POST['voteAbstain'])) {
							$myvote = "Abstain";
						}

						$qvote = "UPDATE TU_VoteInfo SET " . $myvote . " = " . ($row[$myvote] + 1) . " WHERE ID = " . $row['ID'];
						db_query($qvote, $dbh);
						$qvote = "INSERT INTO TU_Votes (VoteID, UserID) VALUES (" . $row['ID'] . ", " . uid_from_sid($_COOKIE["AURSID"]) . ")";
						db_query($qvote, $dbh);

						# Can't vote anymore
						#
						$canvote = 0;
						$errorvote = "You've already voted for this proposal.";
						# Update if they voted
						$hasvoted = mysql_num_rows(db_query($qvoted, $dbh));
						
						$results = db_query($q, $dbh);
						$row = mysql_fetch_assoc($results);
					}
				}

        # I think I understand why MVC is good for this stuff..
				echo "<div class=\"pgbox\">\n";
				echo "  <div class=\"pgboxtitle\"><span class=\"f3\">Proposal Details</span></div>\n";
				echo "  <div class=\"pgboxbody\">\n";

				if ($isrunning == 1) {
					print "<div style='text-align: center; font-weight: bold; color: red'>This vote is still running.</div>";
					print "<br />";
				}

				print "User: <b>";
				
				if (!empty($row['User'])) {
					print "<a href='packages.php?K=" . $row['User'] . "&SeB=m'>" . $row['User'] . "</a>";
				} else {
					print "N/A";
				}	

				print "</b><br />\n";
				
				print "Submitted: <b>" . gmdate("r", $row['Submitted']) . "</b> by ";
				print "<b>" . username_from_id($row['SubmitterID']) . "</b><br />\n";

        if ($isrunning == 0) {
          print "Ended: ";
        } else {
          print "Ends: ";
        }
        print "<b>" . gmdate("r", $row['End']) . "</b><br />\n";

        print "<br />\n";
        
        $row['Agenda'] = htmlentities($row['Agenda']);
				# str_replace seems better than <pre> because it still maintains word wrapping
				print str_replace("\n", "<br />\n", $row['Agenda']);

				print "<br />\n";
				print "<br />\n";
				
				print "<center>\n";
				print "<table cellspacing='3' class='boxSoft' style='width: 50%'>\n";
				print "</tr>\n";
				print "<tr>\n";
				print "  <td class='boxSoft'>\n";
				print "<table width='100%' cellspacing='0' cellpadding='2'>\n";

				print "<tr>\n";
				print "  <th style='border-bottom: #666 1px solid; vertical-align:";
				print " bottom'><span class='f2'>";
				print "Yes";
				print "</span></th>\n";
				print "  <th style='border-bottom: #666 1px solid; vertical-align:";
				print " bottom'><span class='f2'>";
				print "No";
				print "</span></th>\n";
				print "  <th style='border-bottom: #666 1px solid; vertical-align:";
				print " bottom'><span class='f2'>";
				print "Abstain";
				print "</span></th>\n";
				print "  <th style='border-bottom: #666 1px solid; vertical-align:";
				print " bottom'><span class='f2'>";
				print "Total";
				print "</span></th>\n";
				print "  <th style='border-bottom: #666 1px solid; vertical-align:";
				print " bottom'><span class='f2'>";
				print "Voted?";
				print "</span></th>\n";
				print "</tr>\n";

				$c = "data1";

				print "<tr>\n";
				print "  <td class='".$c."'><span class='f5'><span class='blue'>";
				print $row['Yes'];
				print "</span></span></td>\n";
				print "  <td class='".$c."'><span class='f5'><span class='blue'>";
				print $row['No'];
				print "</span></span></td>\n";
				print "  <td class='".$c."'><span class='f5'><span class='blue'>";
				print $row['Abstain'];
				print "</span></span></td>\n";
				print "  <td class='".$c."'><span class='f5'><span class='blue'>";
				print ($row['Yes'] + $row['No'] + $row['Abstain']);
				print "</span></span></td>\n";
				print "  <td class='".$c."'><span class='f5'><span class='blue'>";

				if ($hasvoted == 0) {
					print "<span style='color: red; font-weight: bold'>No</span>";
				} else {
					print "<span style='color: green; font-weight: bold'>Yes</span>";
				}

				print "</span></span></td>\n";
				print "</tr>\n";

				print "</table>\n";
				print "</table>\n";

				echo "</div></div>\n";

				# Actions, vote buttons
				#
				print "<br />\n";
				print "<div class='pgbox'>\n";
				print "<div class='pgboxtitle'><span class='f3'>Vote Actions</span></div>\n";
				print "<div class='pgboxbody'>\n";

				if ($canvote == 1) {
					print "<center><form action='tu.php?id=" . $row['ID'] . "' method='post'>\n";
					print "<input type='submit' class='button' name='voteYes' value='Yes'>\n";
					print "<input type='submit' class='button' name='voteNo' value='No'>\n";
					print "<input type='submit' class='button' name='voteAbstain' value='Abstain'>\n";
					print "<input type='hidden' name='doVote' value='1'>\n";
					print "</form></center>\n";
				} else {
					print "<center>$errorvote</center>";
				}

				print "</div></div>\n";
				print "<br /><center><a href='tu.php'>Back</a></center>\n";

			}

		} else {
			print "Vote ID not valid.\n";
		}

	} else {
		# page listing applications being discussed, voted on and all those finished
		# 

		# I guess there should be a function since I use this a few times
		function gen_results($offset, $limit, $sort, $by, $type="normal") {
			
			$dbh = db_connect();

      if (!empty($offset) AND is_numeric($offset)) {
      	if ($offset >= 1) {
      	  $off = $offset;
     	 	} else {
      	  $off = 0;
    	  }
  	  } else {
  	    $off = 0;
	    }

      $q = "SELECT * FROM TU_VoteInfo";

      if ($type == "new") {	
        $q.= " WHERE End > " . time();
        $application = "Current Votes";
      } else {
        $application = "All Votes";
      }
      
      $order = ($by == 'down') ? 'DESC' : 'ASC';

    	# not much to sort, I'm unsure how to sort by username
    	# when we only store the userid, someone come up with a nifty
    	# way to do this
    	#
    	switch ($sort) {
    	  case 'sub':
    	    $q.= " ORDER BY Submitted $order";
    	    break;
    	  default:
    	    $q.= " ORDER BY Submitted $order";
     	   break;
    	}

    	if ($limit != 0) {
				$q.= " LIMIT " . $off . ", ". $limit;
      }

    	$result = db_query($q, $dbh);
			
			if ($by == "down") {
    	  $by_next = "up";
    	} else {
    	  $by_next = "down";
    	}

    	print "<center>\n";
    	print "<table cellspacing='3' class='boxSoft'>\n";
    	print "<tr>\n";
    	print "  <td class='boxSoftTitle' align='right'>\n";
    	print "    <span class='f3'>$application</span>\n";
    	print "  </td>\n";
    	print "</tr>\n";
    	print "<tr>\n";
    	print "  <td class='boxSoft'>\n";
    	print "<table width='100%' cellspacing='0' cellpadding='2'>\n";

    	print "<tr>\n";
    	print "  <th style='border-bottom: #666 1px solid; vertical-align:";
    	print " bottom'><span class='f2'>";
    	print "Proposal";
    	print "</span></th>\n";
     	print "  <th style='border-bottom: #666 1px solid; vertical-align:";
    	print " bottom'><span class='f2'>";
    	print "<a href='?off=$off&sort=sub&by=$by_next'>Start</a>";
    	print "</span></th>\n";
    	print "  <th style='border-bottom: #666 1px solid; vertical-align:";
    	print " bottom'><span class='f2'>";
    	print "End";
    	print "</span></th>\n";
    	print "  <th style='border-bottom: #666 1px solid; vertical-align:";
    	print " bottom'><span class='f2'>";
    	print "User";
    	print "</span></th>\n";
     	print "  <th style='border-bottom: #666 1px solid; vertical-align:";
    	print " bottom'><span class='f2'>";
    	print "Yes";
    	print "</span></th>\n";
  	 	print "  <th style='border-bottom: #666 1px solid; vertical-align:";
    	print " bottom'><span class='f2'>";
    	print "No";
    	print "</span></th>\n";
# I'm not sure if abstains are necessary inthis view, it's just extra clutter			
#   		print "  <th style='border-bottom: #666 1px solid; vertical-align:";
#    	print " bottom'><span class='f2'>";
#    	print "Abstain";
#    	print "</span></th>\n";
   		print "  <th style='border-bottom: #666 1px solid; vertical-align:";
    	print " bottom'><span class='f2'>";
    	print "Voted?";
    	print "</span></th>\n";
			print "</tr>\n";

    	if (mysql_num_rows($result) == 0) {
     		print "<tr><td align='center' colspan='0'>No results found.</td></tr>\n";
    	} else {
    		for ($i = 0; $row = mysql_fetch_assoc($result); $i++) {
      		# Thankyou AUR

          # alright, I'm going to just have a "new" table and the
          # "old" table can just have every vote, works just as well
          # and probably saves on doing some crap
          #

          (($i % 2) == 0) ? $c = "data1" : $c = "data2";
          print "<tr>\n";
          print "  <td class='".$c."'><span class='f4'><span class='blue'>";
      
          $prev_Len = 100;

          if (strlen($row["Agenda"]) >= $prev_Len) {
            $row["Agenda"] = htmlentities(substr($row["Agenda"], 0, $prev_Len)) . "... -";
          } else {
            $row["Agenda"] = htmlentities($row["Agenda"]) . " -";
          }

          print $row["Agenda"];
          print " <a href='/tu.php?id=" . $row['ID'] . "'>[More]</a>";
          print "</span></span></td>\n";
          print "  <td class='".$c."'><span class='f5'><span class='blue'>";
          # why does the AUR use gmdate with formatting that includes the offset
          # to GMT?!
          print gmdate("j M y", $row["Submitted"]);
          print "</span></span></td>\n";
          print "  <td class='".$c."'><span class='f5'><span class='blue'>";
          print gmdate("j M y", $row["End"]);
          print "</span></span></td>\n";
          print "  <td class='".$c."'><span class='f6'><span class='blue'>";

          if (!empty($row['User'])) {
            print "<a href='packages.php?K=" . $row['User'] . "&SeB=m'>";
            print $row['User'] . "</a>";
          } else {
            print "N/A";
          }

          print "</span></span></td>\n";
          print "  <td class='".$c."'><span class='f5'><span class='blue'>";
          print $row['Yes'];
          print "</span></span></td>\n";
          print "  <td class='".$c."'><span class='f5'><span class='blue'>";
          print $row['No'];
          print "</span></span></td>\n";
          print "  <td class='".$c."'><span class='f5'><span class='blue'>";
          # See above
          # print $row['Abstain'];
          # print "</span></span></td>\n";
          # print "  <td class='".$c."'><span class='f5'><span class='blue'>";

          $qvoted = "SELECT * FROM TU_Votes WHERE ";
          $qvoted.= "VoteID = " . $row['ID'] . " AND ";
          $qvoted.= "UserID = " . uid_from_sid($_COOKIE["AURSID"]);
          $hasvoted = mysql_num_rows(db_query($qvoted, $dbh));

          if ($hasvoted == 0) {
            print "<span style='color: red; font-weight: bold'>No</span>";
          } else {
            print "<span style='color: green; font-weight: bold'>Yes</span>";
          }

          print "</span></span></td>\n";
          print "</tr>\n";
    		}
    	}
		
		print "</table>\n";
    print "</table>\n";

   	if ($type == "old" AND $limit != 0) { 
			$qnext = "SELECT ID FROM TU_VoteInfo";
    	$nextresult = db_query($qnext, $dbh);

    	print "<table style='width: 90%'>\n";

    	if (mysql_num_rows($result)) {
      	$sort = htmlentities($sort, ENT_QUOTES);
      	$by = htmlentities($by, ENT_QUOTES);

      	print "<tr>\n";
      	print "<td align='left'>\n";
      	if ($off != 0) {
      	  $back = (($off - $limit) <= 0) ? 0 : $off - $limit;
      	  print "<a href='tu.php?off=$back&sort=" . $sort . "&by=" . $by . "'>Back</a>";
      	}
      	print "</td>\n";

      	print "<td align='right'>\n";
      	if (($off + $limit) < mysql_num_rows($nextresult)) {
      	  $forw = $off + $limit;
      	  print "<a href='tu.php?off=$forw&sort=" . $sort . "&by=" . $by . "'>Next</a>";
      	}
      	print "</td>\n";
      	print "</tr>\n";
    	}
    	print "</table>\n";
		}

    print "</center>\n";
		}

	# stop notices, ythanku Xilon
	if (empty($_REQUEST['sort'])) { $_REQUEST['sort'] = ""; }
	if (empty($_REQUEST['by'])) { $_REQUEST['by'] = ""; }
	if (empty($_REQUEST['off'])) { $_REQUEST['off'] = ""; }

	gen_results(0, 0, $_REQUEST['sort'], $_REQUEST['by'], "new");
	print "<center><a href='addvote.php'>Add</a></center><br />";
	gen_results($_REQUEST['off'], $pp, $_REQUEST['sort'], $_REQUEST['by'], "old");

	}
} else {
	print "You are not allowed to access this area.\n";
}

html_footer(AUR_VERSION);
# vim: ts=2 sw=2

?>
