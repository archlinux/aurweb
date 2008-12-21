<?php
include_lang('pkgfuncs_po.inc');
include_once("config.inc");

# define variables used during pkgsearch
#
$pkgsearch_vars = array("O", "L", "C", "K", "SB", "SO", "PP", "do_Orphans", "SeB");

# Make sure this visitor can delete the requested package comment
# They can delete if they were the comment submitter, or if they are a TU/Dev
#
function canDeleteComment($comment_id=0, $atype="", $SID="") {
	if ($atype == "Trusted User" || $atype == "Developer") {
		# A TU/Dev can delete any comment
		#
		return TRUE;
	}
	$uid = uid_from_sid($SID);
	$dbh = db_connect();
	$q = "SELECT COUNT(ID) AS CNT ";
	$q.= "FROM PackageComments ";
	$q.= "WHERE ID = " . intval($comment_id);
	$q.= " AND UsersID = " . $uid;
	$result = db_query($q, $dbh);
	if ($result != NULL) {
		$row = mysql_fetch_assoc($result);
		if ($row['CNT'] > 0) {
			return TRUE;
		}
	}
	return FALSE;
}

# see if this Users.ID can manage the package
#
function canManagePackage($uid=0,$AURMUID=0, $MUID=0, $SUID=0, $managed=0) {
	if (!$uid) {return 0;}

	# The uid of the TU/Dev that manages the package
	#
	if ($uid == $AURMUID) {return 1;}

	# If the package isn't maintained by a TU/Dev, is this the user-maintainer?
	#
	if ($uid == $MUID && !$managed) {return 1;}

	# If the package isn't maintained by a TU/Dev, is this the user-submitter?
	#
	if ($uid == $SUID && !$managed) {return 1;}

	# otherwise, no right to manage this package
	#
	return 0;
}

# grab the current list of PackageCategories
#
function pkgCategories() {
	$cats = array();
	$dbh = db_connect();
	$q = "SELECT * FROM PackageCategories WHERE ID != 1 ";
	$q.= "ORDER BY Category ASC";
	$result = db_query($q, $dbh);
	if ($result) {
		while ($row = mysql_fetch_row($result)) {
			$cats[$row[0]] = $row[1];
		}
	}
	return $cats;
}

# grab the current list of PackageLocations
#
function pkgLocations() {
	$locs = array();
	$dbh = db_connect();
	$q = "SELECT * FROM PackageLocations WHERE ID != 1 AND ID < 4 ";
	$q.= "ORDER BY Location ASC";
	$result = db_query($q, $dbh);
	if ($result) {
		while ($row = mysql_fetch_row($result)) {
			$locs[$row[0]] = $row[1];
		}
	}
	return $locs;
}

# check to see if the package name exists
#
function package_exists($name="") {
	if (!$name) {return NULL;}
	$dbh = db_connect();
	$q = "SELECT ID FROM Packages ";
	$q.= "WHERE Name = '".mysql_real_escape_string($name)."' ";
	$q.= "AND DummyPkg = 0";
	$result = db_query($q, $dbh);
	if (!$result) {return NULL;}
	$row = mysql_fetch_row($result);
	return $row[0];
}

# grab package dependencies
#
function package_dependencies($pkgid=0) {
	$deps = array();
	if ($pkgid) {
		$dbh = db_connect();
		$q = "SELECT DepPkgID, Name, DummyPkg, DepCondition FROM PackageDepends, Packages ";
		$q.= "WHERE PackageDepends.DepPkgID = Packages.ID ";
		$q.= "AND PackageDepends.PackageID = ".mysql_real_escape_string($pkgid);
		$q.= " ORDER BY Name";
		$result = db_query($q, $dbh);
		if (!$result) {return array();}
		while ($row = mysql_fetch_row($result)) {
			$deps[] = $row;
		}
	}
	return $deps;
}

function package_required($pkgid=0) {
	$deps = array();
	if ($pkgid) {
		$dbh = db_connect();
		$q = "SELECT PackageID, Name, DummyPkg from PackageDepends, Packages ";
		$q.= "WHERE PackageDepends.PackageID = Packages.ID ";
		$q.= "AND PackageDepends.DepPkgID = ";
		$q.= mysql_real_escape_string($pkgid);
		$q.= " ORDER BY Name";
		$result = db_query($q, $dbh);
		if (!$result) {return array();}
		while ($row = mysql_fetch_row($result)) {
			$deps[] = $row;
		}
	}
	return $deps;
}

# create a dummy package and return it's Packages.ID  if it already exists,
# return the existing ID
#
function create_dummy($pname="", $sid="") {
	if ($pname && $sid) {
		$uid = uid_from_sid($sid);
		if (!$uid) {return NULL;}
		$dbh = db_connect();
		$q = "SELECT ID FROM Packages WHERE Name = '";
		$q.= mysql_real_escape_string($pname)."'";
		$result = db_query($q, $dbh);
		if (!mysql_num_rows($result)) {
			# Insert the dummy
			#
			$q = "INSERT INTO Packages (Name, Description, URL, SubmittedTS, ";
			$q.= "SubmitterUID, DummyPkg) VALUES ('";
			$q.= mysql_real_escape_string($pname)."', 'A dummy package', '/#', ";
			$q.= "UNIX_TIMESTAMP(), ".$uid.", 1)";
			$result = db_query($q, $dbh);
			if (!$result) {
				return NULL;
			}
			return mysql_insert_id($dbh);
		} else {
			$data = mysql_fetch_row($result);
			return $data[0];
		}
	}
	return NULL;

}

# grab package comments
#
function package_comments($pkgid=0) {
	$comments = array();
	if ($pkgid) {
		$dbh = db_connect();
		$q = "SELECT PackageComments.ID, UserName, UsersID, Comments, CommentTS ";
		$q.= "FROM PackageComments, Users ";
		$q.= "WHERE PackageComments.UsersID = Users.ID";
		$q.= " AND PackageID = ".mysql_real_escape_string($pkgid);
		$q.= " AND DelUsersID = 0"; # only display non-deleted comments
		$q.= " ORDER BY CommentTS DESC";
		$result = db_query($q, $dbh);
		if (!$result) {return array();}
		while ($row = mysql_fetch_assoc($result)) {
			$comments[] = $row;
		}
	}
	return $comments;
}

# grab package sources
#
function package_sources($pkgid=0) {
	$sources = array();
	if ($pkgid) {
		$dbh = db_connect();
		$q = "SELECT Source FROM PackageSources ";
		$q.= "WHERE PackageID = ".mysql_real_escape_string($pkgid);
		$q.= " ORDER BY Source";
		$result = db_query($q, $dbh);
		if (!$result) {return array();}
		while ($row = mysql_fetch_row($result)) {
			$sources[] = $row[0];
		}
	}
	return $sources;
}


# grab array of Package.IDs that I've voted for: $pkgs[1234] = 1, ...
#
function pkgvotes_from_sid($sid="") {
	$pkgs = array();
	if (!$sid) {return $pkgs;}
	$dbh = db_connect();
	$q = "SELECT PackageID ";
	$q.= "FROM PackageVotes, Users, Sessions ";
	$q.= "WHERE Users.ID = Sessions.UsersID ";
	$q.= "AND Users.ID = PackageVotes.UsersID ";
	$q.= "AND Sessions.SessionID = '".mysql_real_escape_string($sid)."'";
	$result = db_query($q, $dbh);
	if ($result) {
		while ($row = mysql_fetch_row($result)) {
			$pkgs[$row[0]] = 1;
		}
	}
	return $pkgs;
}

# array of package ids that you're being notified for
# *yoink*
#
function pkgnotify_from_sid($sid="") {
	$pkgs = array();
	if (!$sid) {return $pkgs;}
	$dbh = db_connect();
	$q = "SELECT PkgID ";
	$q.= "FROM CommentNotify, Users, Sessions ";
	$q.= "WHERE Users.ID = Sessions.UsersID ";
	$q.= "AND Users.ID = CommentNotify.UserID ";
	$q.= "AND Sessions.SessionID = '".mysql_real_escape_string($sid)."'";
	$result = db_query($q, $dbh);
	if ($result) {
		while ($row = mysql_fetch_row($result)) {
			$pkgs[$row[0]] = 1;
		}
	}
	return $pkgs;
}

# get name of package based on pkgid
#
function pkgname_from_id($id="") {
	if (!empty($id)) {
		$dbh = db_connect();
		$id = intval($id);
		$q = "SELECT Name FROM Packages WHERE ID = " . mysql_real_escape_string($id);
		$result = db_query($q, $dbh);
		if (mysql_num_rows($result) > 0) {
			$id = mysql_result($result, 0);
		} else {
			$id = "";
		}
	}
	return $id;
}

# display package details
#
function package_details($id=0, $SID="") {
	global $_REQUEST;
	global $pkgsearch_vars;
	$q = "SELECT Packages.*,Location,Category ";
	$q.= "FROM Packages,PackageLocations,PackageCategories ";
 	$q.= "WHERE Packages.LocationID = PackageLocations.ID ";
	$q.= "AND Packages.CategoryID = PackageCategories.ID ";
	$q.= "AND Packages.ID = ".intval($_REQUEST["ID"]);
	$dbh = db_connect();
	$results = db_query($q, $dbh);
	if (!$results) {
		print __("Error retrieving package details.")."<br />\n";

	} else {
		$row = mysql_fetch_assoc($results);
		if (empty($row)) {
			print __("Package details could not be found.")."<br />\n";

		} else {

			# print out package details
			#
			echo "<div class=\"pgbox\">\n";
			echo "  <div class=\"pgboxtitle\"><span class=\"f3\">".__("Package Details")."</span></div>\n";
			echo "  <div class=\"pgboxbody\">\n";
			echo "    <table>\n";
			echo "      <tr><td class='boxSoft' colspan='2'><span class='f2'>";
			echo $row["Name"] . " " . $row["Version"]."</span></td></tr>\n";
			echo "      <tr><td class='boxSoft' colspan='2'><span class='f3'>";
			echo "<a href='".$row["URL"]."'>".$row["URL"]."</a></span></td></tr>\n";
			echo "      <tr><td class='boxSoft' colspan='2'><span class='f3'>".$row["Description"];
			echo "</a></span></td></tr>\n";
			echo "      <tr><td class='boxSoft' colspan='2'><img src='/images/pad.gif' height='30'></td></tr>\n";
			echo "      <tr><td class='boxSoft' colspan='2'><span class='f3'>";
			if ($row["Location"] == "unsupported" and ( 
					uid_from_sid($SID) == $row["MaintainerUID"] or
					(account_from_sid($SID) == "Developer" or
					 account_from_sid($SID) == "Trusted User"))) {
			  $edit_cat = "<a href='pkgedit.php?change_Category=1&ID=";
			  $edit_cat .= intval($_REQUEST["ID"])."'>".$row["Category"]."</a>";
			  $edit_cat .= " &nbsp;<span class='fix'>(";
			  $edit_cat .= __("change category").")</span>";
			} else {
				$edit_cat = $row["Category"];
			}
			echo $row["Location"]." :: ".$edit_cat."</span></td></tr>\n";
			echo "        <tr><td class='boxSoft' colspan='2'><span class='f3'>".__("Maintainer").": ";
			if ($row["MaintainerUID"]) {
				$maintainer = username_from_id($row["MaintainerUID"]);
				if ($SID) {
					echo "<a href='account.php?Action=AccountInfo&ID=";
					echo $row["MaintainerUID"] . "'>";
					echo $maintainer . "</a></span></td>";
				} else {
					echo $maintainer . "</span></td>";
				}
			} else {
				$maintainer = "None";
				echo $maintainer . "</span></td>";
			}
			echo "      </tr>\n";
			echo "      <tr><td class='boxSoft' colspan='2'><span class='f3'>".__("Votes").": ";
			echo $row["NumVotes"] . "</span></td></tr>\n";
            
            # In case of wanting to put a custom message
            $msg = __("unknown");
            $license = $row["License"] == "" ? $msg : $row["License"];
            
            echo "      <tr><td class='boxSoft' colspan='2'><br><span class='f3'>".__("License").": ".$license;
            echo "</a></span></td></tr>\n";            
			echo "      <tr><td class='boxSoft' colspan='2'><img src='/images/pad.gif' height='15'></td></tr>\n";

			# Print the timestamps for last updates
			$updated_time = ($row["ModifiedTS"] == 0) ? "(unknown)" : gmdate("r", intval($row["ModifiedTS"]));
			$submitted_time = ($row["SubmittedTS"] == 0) ? "(unknown)" : gmdate("r", intval($row["SubmittedTS"]));
			echo "      <tr><td class='boxSoft' colspan='2'><span class='f3'>";
			echo __("Last Updated").": ".$updated_time."<br>";
			echo __("First Submitted").": ".$submitted_time."</span></td></tr>\n";
			echo "      <tr><td class='boxSoft' colspan='2'><img src='/images/pad.gif' height='15'></td></tr>\n";
			echo "      <tr><td class='boxSoft' colspan='2'><span class='f3'>";
			if ($row["LocationID"] == 2) {
				$urlpath = URL_DIR.$row["Name"]."/".$row["Name"];
				print "<a href='$urlpath.tar.gz'>".__("Tarball")."</a> :: <a href='$urlpath'>".__("Files")."</a> :: <a href='$urlpath/PKGBUILD'>PKGBUILD</a></span></td>";
			} elseif ($row["LocationID"] == 3) {
			  echo "<a href='http://repos.archlinux.org/viewvc.cgi/community/" . $row["Category"] . "/" . $row["Name"] . "/?root=community&pathrev=CURRENT'>CVS</td>";
			}
			echo "</tr>\n";
			if ($row["OutOfDate"] == 1) {
				echo "\n<tr><td colspan='2'>";
				echo "<span class='f6'>".__("This package has been flagged out of date.")."</span></td></tr>";
			}
			echo "      <tr><td class='boxSoft' colspan='2'><img src='/images/pad.gif' height='30'></td></tr>\n";
			
			$deps = package_dependencies($row["ID"]); # $deps[0] = array('id','name', 'dummy');
			if (count($deps) > 0) {
			
			echo "      <tr>\n";
			echo "        <td valign='top' style='padding-right: 10'>\n";
  			echo "          <table class='boxSoft' style='width: 200px'>\n";
  			echo "            <tr><td class='boxSoftTitle'><span class='f3'>";
  			echo __("Dependencies")."</span></td></tr>\n";
  			echo "            <tr><td class='boxSoft'>";
  			
				while (list($k, $darr) = each($deps)) {
					$url = "<a href='packages.php?ID=".$darr[0];
					while(list($k, $var) = each($pkgsearch_vars)) {
						if (($var == "do_Orphans") && $_REQUEST[$var]) {
							$url .= "&".$var."=1";
						} else {
							$url .= "&".$var."=".rawurlencode(stripslashes($_REQUEST[$var]));
						}
					}
					reset($pkgsearch_vars);
																								 
									// $darr[3] is the DepCondition                                               
																								 
					if ($darr[2] == 0) echo $url."'>".$darr[1].$darr[3]."</a><br />\n";
					else echo "<a href='http://archlinux.org/packages/search/?q=".$darr[1]."'>".$darr[1].$darr[3]."</a><br />\n";
				}
			
  			echo "</td></tr>\n";
  			echo "</table></td>";

      }

			$deps = package_required($row["ID"]);
			if (count($deps) > 0) {
			  
  			echo "  <td valign='top'>";
  			echo "<table class='boxSoft' style='width: 200px'>";
  			echo "<tr><td class='boxSoftTitle'><span class='f3'>";
  			echo __("Required by")."</span></td></tr>\n";
  			echo "<tr><td class='boxSoft'>";

				while (list($k, $darr) = each($deps)) {
					$url = "<a href='packages.php?ID=".$darr[0];
					while(list($k, $var) = each($pkgsearch_vars)) {
						if (($var == "do_Orphans") && $_REQUEST[$var]) {
							$url .= "&".$var."=1";
						} else {
							$url .= "&".$var."=".rawurlencode(stripslashes($_REQUEST[$var]));
						}
					}
					reset($pkgsearch_vars);
																								 
									// $darr[3] is the DepCondition                                               
																								 
					if ($darr[2] == 0) print $url."'>".$darr[1].$darr[3]."</a><br />\n";
					else print "<a href='http://archlinux.org/packages/search/?q=".$darr[1]."'>".$darr[1].$darr[3]."</a><br />\n";
				}

  			echo "</td></tr>\n";
  			echo "          </table>\n";
  			echo "        </td>\n";
			
		  }
			
			$sources = package_sources($row["ID"]); # $sources[0] = 'src';
			if (count($sources) > 0) {
			
  			echo "        <td valign='top'>\n";
  			echo "          <table class='boxSoft' style='width: 200px'>\n";
  			echo "            <tr><td class='boxSoftTitle'><span class='f3'>";
  			echo __("Sources")."</span></td></tr>\n";
  			echo "            <tr><td class='boxSoft'>";

				while (list($k, $src) = each($sources)) {
					$parsed_url = parse_url($src);
					if ($parsed_url['scheme'])
					{
						//It is an external source
						echo "<a href='".$src."'>".$src."</a><br />\n";
					}
					else 
					{
						//It is presumably an internal source
						if ($row["LocationID"] == 2) {
							echo "<a href='".dirname($row['URLPath'])."/".$row['Name'];
							echo "/".$src."'>".$src."</a><br />\n";
						} elseif ($row["LocationID"] == 3) {
							echo "<a href='http://repos.archlinux.org/viewvc.cgi/community/" . $row["Category"] . "/" . $row["Name"] . "/?root=community&pathrev=CURRENT'>";
							echo $src."</a><br />\n";
						}
					}
				}
			
  			echo "</td></tr>\n";
  			echo "          </table>\n";
  			echo "        </td>\n";
			
		  }
		
			echo "      </tr>\n";
			echo "    </table>\n";
			echo "  </div>\n";
			echo "</div>\n\n";
			echo "<br />\n\n";


			# Actions Bar
			#
			if ($SID) {
                echo "<div class=\"pgbox\">\n";
                echo "  <div class=\"pgboxtitle\"><span class=\"f3\">".__("Actions")."</span></div>\n";
                echo "  <div class=\"pgboxbody\">\n";
                echo "    <form action='packages.php?ID=".$row['ID']."' method='post'>\n";
				echo "      <input type='hidden' name='IDs[".$row["ID"]."]' value='1'>\n";
				echo "      <input type='hidden' name='ID' value='".$row["ID"]."'>\n";
				# Voting Button
				#
				$q = "SELECT * FROM PackageVotes WHERE UsersID = ".uid_from_sid($SID);
				$q.= " AND PackageID = ".$row["ID"];
				if (!mysql_num_rows(db_query($q, $dbh))) {
					echo "      <input type='submit' class='button' name='do_Vote'";
					echo " value='".__("Vote")."'>";
				} else {
					echo "<input type='submit' class='button' name='do_UnVote'";
					echo " value='".__("UnVote")."'>";
				}
				# Comment Nofify Button
				#
				$q = "SELECT * FROM CommentNotify WHERE UserID = ".uid_from_sid($SID);
				$q.= " AND PkgID = ".$row["ID"];
				if (!mysql_num_rows(db_query($q, $dbh))) {
					echo "<input type='submit' class='button' name='do_Notify'";
					echo " value='".__("Notify")."' title='".__("New Comment Notification")."'>";
				} else {
					echo "<input type='submit' class='button' name='do_UnNotify'";
					echo " value='".__("UnNotify")."' title='".__("No New Comment Notification")."'>";
				}

                if ($row["OutOfDate"] == 0) {
                    echo "<input type='submit' class='button' name='do_Flag'";
                    echo " value='".__("Flag Out-of-date")."'>\n";
                } else {
                    echo "<input type='submit' class='button' name='do_UnFlag'";
                    echo " value='".__("UnFlag Out-of-date")."'>\n";
				}
					
                if ($row["MaintainerUID"] == 0) {
                    echo "<input type='submit' class='button' name='do_Adopt'";
                    echo " value='".__("Adopt Packages")."'>\n";
                } else if ($row["MaintainerUID"] == uid_from_sid($SID) ||
            	           account_from_sid($SID) == "Trusted User" ||
            	           account_from_sid($SID) == "Developer") {
					echo "<input type='submit' class='button' name='do_Disown'";
					echo " value='".__("Disown Packages")."'>\n";
				}
					
				if (account_from_sid($SID) == "Trusted User" ||
				    account_from_sid($SID) == "Developer") {
					echo "<input type='submit' class='button' name='do_Delete'";
					echo " value='".__("Delete Packages")."'>\n";
				}
						
                echo "    </form>\n";
                echo "  </div>\n";
                echo "</div>\n";
                echo "\n<br />\n\n";
			}
			
			# Comments
			#
			echo "<div class=\"pgbox\">\n";
			echo "  <div class=\"pgboxtitle\"><span class=\"f3\">".__("Comments")."</span></div>\n";
			echo "  <div class=\"pgboxbody-comment\">\n";
			echo "    <table width='100%'>\n";
			if (isset($_COOKIE['AURSID'])) {
				echo "<tr><td>";
				echo "          <form action='pkgedit.php' method='post'>\n";
				echo "            <input type='hidden' name='ID' value='".$row["ID"]."'>\n";
				echo "            <input type='submit' class='button' name='add_Comment' value=\"";
				echo __("Add Comment")."\">\n";
				echo "          </form>\n";
				echo "</tr></td>";
				//echo "<br />\n";
			}
			$comments = package_comments($row["ID"]);
			if (!empty($comments)) {
				while (list($indx, $carr) = each($comments)) {

					echo "      <tr>\n";
					echo "        <td valign='top' style='padding-right: 10' colspan='2'>\n";
					echo "          <table class='boxSoft' width='100%'>\n";
					echo "            <tr>\n";
					echo "              <td class='boxSoftTitle'><span class='f3'>";
					if (canDeleteComment($carr["ID"], account_from_sid($SID), $SID)) {
						$durl = "<a href='pkgedit.php?del_Comment=1";
						$durl.= "&comment_id=".$carr["ID"]."&ID=".$row["ID"];
						$durl.= "'><img src='/images/x.png' border='0'";
						$durl.= " alt=\"".__("Delete comment")."\"></a>";

					  echo $durl . "&nbsp;&nbsp;";
					}
					if ($SID) {
						echo __("Comment by: %h%s%h on %h%s%h",
							array("<a href='account.php?Action=AccountInfo&ID=".$carr["UsersID"]."'><b>",$carr["UserName"],"</b></a>",
							      "<i>",gmdate("Ymd [H:i:s]",$carr["CommentTS"]),"</i>"));
					} else {
						echo __("Comment by: %h%s%h on %h%s%h",
							array("<b>",$carr["UserName"],"</b>",
							      "<i>",gmdate("Ymd [H:i:s]",$carr["CommentTS"]),"</i>"));
					}
					echo "</span></td>\n";
					echo "            </tr>\n";
					echo "            <tr>\n";
					echo "              <td class='boxSoft'>";
					echo "<code>\n";
					echo nl2br(htmlspecialchars($carr["Comments"]));
					echo "</code></td>\n";
					echo "            </tr>\n";
					echo "          </table>\n";
					echo "        </td>\n";
					echo "      </tr>\n";
				}
			} else {
				print "<tr><td>None</td></tr>\n";
			}
			echo "    </table>\n";
			echo "  </div>\n";
			echo "</div>\n";
		}
	}
	return;
}


/* pkg_search_page(SID)
 * outputs the body of search/search results page
 *
 * parameters:
 *  SID - current Session ID
 * preconditions:
 *  package search page has been accessed
 *  request variables have not been sanitized
 *
 *  request vars:
 *    O  - starting result number
 *    PP - number of search hits per page
 *    L  - package location ID number
 *    C  - package category ID number
 *    K  - package search string
 *    SO - search hit sort order:
 *          values: a - ascending
 *                  d - descending
 *    SB - sort search hits by:
 *          values: l - package location
 *                  c - package category
 *                  n - package name
 *                  v - number of votes
 *                  m - maintainer username
 *    SeB- property that search string (K) represents
 *          values: nd - package name&description
 *                  m  - package maintainer's username
 *                  s  - package submitter's username
 *    do_Orphans    - boolean. whether to search packages
 *                     without a maintainer
 *
 *
 *    These two are actually handled in packages.php.
 *
 *    IDs- integer array of ticked packages' IDs
 *    action - action to be taken on ticked packages
 *             values: do_Flag   - Flag out-of-date
 *                     do_UnFlag - Remove out-of-date flag
 *                     do_Adopt  - Adopt
 *                     do_Disown - Disown
 *                     do_Delete - Delete
 *                     do_Notify - Enable notification
 *                     do_UnNotify - Disable notification
 */
function pkg_search_page($SID="") {
    // establish a db connection
    $dbh = db_connect();

    // get commonly used variables...
    // TODO: REDUCE DB HITS.
    // grab info for user if they're logged in
    if ($SID)
        $myuid = uid_from_sid($SID);
    // get a list of package locations
    $locs = pkgLocations();
    // get a list of package categories
    $cats = pkgCategories(); //meow

    // sanitize paging variables
    //
    if (isset($_REQUEST['O'])) {
        $O = intval($_REQUEST['O']);
        if ($O < 0)
            $O = 0;
    } else {
        $O = 0;
    }

    if (isset($_REQUEST["PP"])) {
        $PP = intval($_REQUEST["PP"]);
        if ($PP < 25)
            $PP = 25;
        else if ($PP > 100)
            $PP = 100;
    } else {
        $PP = 25;
    }

    include('../template/pkg_search_form.php');

    // FIXME: pull out DB-related code. all of it.
    //        this one's worth a choco-chip cookie,
    //        one of those nice big soft ones

    // build the package search query
    //
    $q = "SELECT SQL_CALC_FOUND_ROWS ";
    if ($SID) {
        $q .= "CommentNotify.UserID AS Notify,
               PackageVotes.UsersID AS Voted, ";
    }
    $q .= "Users.Username AS Maintainer,
        PackageCategories.Category,
        PackageLocations.Location,
        Packages.Name, Packages.Version, Packages.Description, Packages.NumVotes,
        Packages.ID, Packages.OutOfDate

        FROM PackageCategories, PackageLocations, Packages
        LEFT JOIN Users ON (Packages.MaintainerUID = Users.ID) ";
    if ($SID) {
        $q .= "LEFT JOIN PackageVotes
                ON (Packages.ID = PackageVotes.PackageID AND PackageVotes.UsersID = ".$myuid.")
               LEFT JOIN CommentNotify
                ON (Packages.ID = CommentNotify.PkgID AND CommentNotify.UserID = ".$myuid.") ";
    }
    $q .= "WHERE
        Packages.CategoryID = PackageCategories.ID
        AND Packages.LocationID = PackageLocations.ID
        AND Packages.DummyPkg = 0 ";

    // TODO: possibly do string matching on category and
    //       location to make request variable values more sensible
    if (intval($_REQUEST["L"])) {
        $q .= "AND Packages.LocationID = ".intval($_REQUEST["L"])." ";
    }
    if (intval($_REQUEST["C"])) {
        $q.= "AND Packages.CategoryID = ".intval($_REQUEST["C"])." ";
    }

    if ($_REQUEST['K']) {
        $K = mysql_real_escape_string(trim($_REQUEST['K']));
        //search by maintainer
        if ($_REQUEST["SeB"] == "m"){
            $q.= "AND Users.Username = '".$K."' ";
        } elseif ($_REQUEST["SeB"] == "s") {
            // FIXME: this shouldn't be making 2 queries
            //        kill the call to uid_from_username
            $q.= "AND SubmitterUID = ".uid_from_username($_REQUEST['K'])." ";
        // the default behavior, query the name/description
        } else {
            $q.= "AND (Name LIKE '%".$K."%' OR ";
            $q.= "Description LIKE '%".$K."%') ";
        }
    }

    if ($_REQUEST["do_Orphans"]) {
        $q.= "AND MaintainerUID = 0 ";
    }

    $order = $_REQUEST["SO"] == 'd' ? 'DESC' : 'ASC';

    switch ($_REQUEST["SB"]) {
        case 'c':
            $q.= "ORDER BY CategoryID ".$order.", Name ASC, LocationID ASC ";
            $SB = 'c';
            break;
        case 'l':
            $q.= "ORDER BY LocationID ".$order.", Name ASC, CategoryID DESC ";
            $SB = 'l';
            break;
        case 'v':
            $q.= "ORDER BY NumVotes ".$order.", Name ASC, CategoryID DESC ";
            $SB = 'v';
            break;
        case 'm':
            $q.= "ORDER BY Maintainer ".$order.", Name ASC, LocationID ASC ";
            $SB = 'm';
            break;
        case 'a':
            $q.= "ORDER BY GREATEST(SubmittedTS,ModifiedTS) ".$order.", Name ASC, LocationID ASC ";
            $SB = 'a';
            break;
        default:
            $q.= "ORDER BY Name ".$order.", LocationID ASC, CategoryID DESC ";
            break;
    }

    $q.= "LIMIT ".$O.", ".$PP;

    $result = db_query($q, $dbh);
    $total = mysql_result(db_query('SELECT FOUND_ROWS() AS Total', $dbh), 0);

	if ($result && $total > 0) {
	    if ($_REQUEST["SO"] == "d"){
	        $SO_next="a";
	        $SO = 'd';
	    } else {
	        $SO_next="d";
	        $SO = 'a';
	    }
	}

	// figure out the results to use
    $first = $O + 1;

    if (($PP+$O) > $total) {
        $last = $total;
    } else {
        $last = $PP + $O;
    }

	include('pkg_search_results.php');

    return;
}

/**
 * Flag and un-flag packages out-of-date
 *
 * @param string $atype Account type, output of account_from_sid
 * @param array $ids Array of package IDs to flag/unflag
 * @param boolean $action True flags out-of-date, false un-flags. Flags by
 * default
 *
 * @return string Translated success or error messages
 */
function pkg_flag ($atype, $ids, $action = True) {
	if (!$atype) {
		if ($action) {
			return __("You must be logged in before you can flag packages.");
		} else {
			return __("You must be logged in before you can unflag packages.");
		}
	}

	if (empty($ids)) {
		if ($action) {
			return __("You did not select any packages to flag.");
		} else {
			return __("You did not select any packages to unflag.");
		}
	}

	foreach ($ids as $pid) {
		if (!is_numeric($pid)) {
			if ($action) {
				return __("You did not select any packages to flag.");
			} else {
				return __("You did not select any packages to unflag.");
			}
		}
	}

	$dbh = db_connect();

	$first = 1;
	foreach ($ids as $pid) {
		if ($first) {
			$first = 0;
			$flag = $pid;
		} else {
			$flag .= ", " . $pid;
		}
	}

	$ood = $action ? 1 : 0;
	$q = "UPDATE Packages SET OutOfDate = " . $ood;
	$q.= " WHERE ID IN (" . $flag . ")";

	db_query($q, $dbh);

	if ($action) {
		# Notify of flagging by email
		$f_name = username_from_sid($_COOKIE['AURSID']);
		$f_email = email_from_sid($_COOKIE['AURSID']);
		$f_uid = uid_from_sid($_COOKIE['AURSID']);
		$q = "SELECT Packages.Name, Users.Email, Packages.ID ";
		$q.= "FROM Packages, Users ";
		$q.= "WHERE Packages.ID IN (" . $flag .") ";
		$q.= "AND Users.ID = Packages.MaintainerUID ";
		$q.= "AND Users.ID != " . $f_uid;
		$result = db_query($q, $dbh);
		if (mysql_num_rows($result)) {
			while ($row = mysql_fetch_assoc($result)) {
				# construct email
				$body = "Your package " . $row['Name'] . " has been flagged out of date by " . $f_name . ". You may view your package at:\nhttp://aur.archlinux.org/packages.php?ID=" . $row['ID'];
				$body = wordwrap($body, 70);
				$headers = "To: ".$row['Email']."\nReply-to: nobody@archlinux.org\nFrom:aur-notify@archlinux.org\nX-Mailer: PHP\nX-MimeOLE: Produced By AUR\n";
				@mail(' ', "AUR Out-of-date Notification for ".$row['Name'], $body, $headers);
			}
		}
	}

	if ($action) {
		return __("The selected packages have been flagged out-of-date.");
	} else {
		return __("The selected packages have been unflagged.");
	}
}

/**
 * Delete packages
 *
 * @param string $atype Account type, output of account_from_sid
 * @param array $ids Array of package IDs to delete
 *
 * @return string Translated error or success message
 */
function pkg_delete ($atype, $ids) {
	if (!$atype) {
		return __("You must be logged in before you can disown packages.");
	}

	if (empty($ids)) {
		return __("You did not select any packages to delete.");
	}

	# Delete the packages in $ids array (but only if they are Unsupported)
	#
	$dbh = db_connect();

	# Delete the packages in $ids array
	#
	$first = 1;
	foreach ($ids as $pid) {
		if ($first) {
			$first = 0;
			$delete = $pid;
		} else {
			$delete .= ", ".$pid;
		}
	}

	$field = "MaintainerUID";

	# Only grab Unsupported packages that "we" own or are not owned at all
	$ids_to_delete = array();
	$q = "SELECT Packages.ID FROM Packages, PackageLocations ";
	$q.= "WHERE Packages.ID IN (" . $delete . ") ";
	$q.= "AND Packages.LocationID = PackageLocations.ID ";
	$q.= "AND PackageLocations.Location = 'unsupported' ";

	# If they're a TU or dev, can delete
	if ($atype == "Trusted User" || $atype == "Developer") {
		$result = db_query($q, $dbh);
	}

	if ($result != Null && mysql_num_rows($result) > 0) {
		while ($row = mysql_fetch_assoc($result)) {
			$ids_to_delete[] = $row['ID'];
		}
	}

	if (empty($ids_to_delete)) {
		return __("None of the selected packages could be deleted.");
	}

	# These are the packages that are safe to delete
	foreach ($ids_to_delete as $id) {
		$q = "DELETE FROM PackageVotes WHERE PackageID = " . $id;
		$result = db_query($q, $dbh);

		$q = "DELETE FROM PackageDepends WHERE PackageID = " . $id;
		$result = db_query($q, $dbh);

		$q = "DELETE FROM PackageSources WHERE PackageID = " . $id;
		$result = db_query($q, $dbh);

		$q = "DELETE FROM PackageComments WHERE PackageID = " . $id;
		$result = db_query($q, $dbh);

		$q = "DELETE FROM Packages WHERE ID = " . $id;
		$result = db_query($q, $dbh);

		$q = "DELETE FROM CommentNotify WHERE PkgID = " . $id;
		$result = db_query($q, $dbh);
	}

	return __("The selected packages have been deleted.");
}

/**
 * Adopt or disown packages
 *
 * @param string $atype Account type, output of account_from_sid
 * @param array $ids Array of package IDs to adopt/disown
 * @param boolean $action Adopts if true, disowns if false. Adopts by default
 *
 * @return string Translated error or success message
 */
function pkg_adopt ($atype, $ids, $action = True) {
	if (!$atype) {
		if ($action) {
			return __("You must be logged in before you can adopt packages.");
		} else {
			return __("You must be logged in before you can disown packages.");
		}
	}

	if (empty($ids)) {
		if ($action) {
			return __("You did not select any packages to adopt.");
		} else {
			return __("You did not select any packages to disown.");
		}
	}

	$dbh = db_connect();

	$first = 1;
	foreach ($ids as $pid) {
		if ($first) {
			$first = 0;
			$pkg = $pid;
		} else {
			$pkg .= ", ".$pid;
		}
	}

	$field = "MaintainerUID";
	$q = "UPDATE Packages ";

	if ($action) {
		$user = uid_from_sid($_COOKIE["AURSID"]);
	} else {
		$user = 0;
	}

	$q.= "SET $field = $user ";
	$q.= "WHERE ID IN ($pkg) ";

	if ($action && $atype == "User") {
		# Regular users may only adopt orphan packages from unsupported
		$q.= "AND $field = 0 ";
		$q.= "AND LocationID = 2 ";
	} else if ($atype == "User") {
		$q.= "AND $field = " . uid_from_sid($_COOKIE["AURSID"]);
	}

	db_query($q, $dbh);

	if ($action) {
		return __("The selected packages have been adopted.");
	} else {
		return __("The selected packages have been disowned.");
	}
}

/**
 * Vote and un-vote for packages
 *
 * @param string $atype Account type, output of account_from_sid
 * @param array $ids Array of package IDs to vote/un-vote
 * @param boolean $action Votes if true, un-votes if false. Votes by default
 *
 * @return string Translated error or success message
 */
function pkg_vote ($atype, $ids, $action = True) {
	if (!$atype) {
		if ($action) {
			return __("You must be logged in before you can vote for packages.");
		} else {
			return __("You must be logged in before you can un-vote for packages.");
		}
	}

	if (empty($ids)) {
		if ($action) {
			return __("You did not select any packages to vote for.");
		} else {
			return __("Your votes have been removed from the selected packages.");
		}
	}

	$dbh = db_connect();
	$my_votes = pkgvotes_from_sid($_COOKIE["AURSID"]);
	$uid = uid_from_sid($_COOKIE["AURSID"]);

	$first = 1;
	foreach ($ids as $pid) {
		if ($action) {
			$check = !isset($my_votes[$pid]);
		} else {
			$check = isset($my_votes[$pid]);
		}

		if ($check) {
			if ($first) {
				$first = 0;
				$vote_ids = $pid;
				if ($action) {
					$vote_clauses = "($uid, $pid)";
				}
			} else {
				$vote_ids .= ", $pid";
				if ($action) {
					$vote_clauses .= ", ($uid, $pid)";
				}
			}
		}
	}

	# only vote for packages the user hasn't already voted for
	#
	$op = $action ? "+" : "-";
	$q = "UPDATE Packages SET NumVotes = NumVotes $op 1 ";
	$q.= "WHERE ID IN ($vote_ids)";

	db_query($q, $dbh);

	if ($action) {
		$q = "INSERT INTO PackageVotes (UsersID, PackageID) VALUES ";
		$q.= $vote_clauses;
	} else {
		$q = "DELETE FROM PackageVotes WHERE UsersID = $uid ";
		$q.= "AND PackageID IN ($vote_ids)";
	}

	db_query($q, $dbh);

	if ($action) {
		$q = "UPDATE Users SET LastVoted = UNIX_TIMESTAMP() ";
		$q.= "WHERE ID = $uid";

		db_query($q, $dbh);
	}

	if ($action) {
		return __("Your votes have been cast for the selected packages.");
	} else {
		return __("Your votes have been removed from the selected packages.");
	}
}

/**
 * Toggle notification of packages
 *
 * @param string $atype Account type, output of account_from_sid
 * @param array $ids Array of package IDs to toggle, formatted as $package_id
 * @return string Translated error or success message
 */
function pkg_notify ($atype, $ids, $action = True) {
	if (!$atype) {
#		return __("You must be logged in before you can get notifications on comments.");
		return;
	}

	if (empty($ids)) {
		return __("Couldn't add to notification list.");
	}

	$dbh = db_connect();
	$uid = uid_from_sid($_COOKIE["AURSID"]);

	$output = "";

	$first = True;

	# There currently shouldn't be multiple requests here, but the
	# format in which it's sent requires this.
	foreach ($ids as $pid) {
		$q = "SELECT Name FROM Packages WHERE ID = $pid";
		$pkgname = mysql_result(db_query($q, $dbh), 0);

		if ($first)
			$first = False;
		else
			$output .= ", ";


		if ($action) {
			$q = "SELECT * FROM CommentNotify WHERE UserID = $uid";
			$q .= " AND PkgID = $pid";

			# Notification already added. Don't add again.
			if (!mysql_num_rows(db_query($q, $dbh))) {
				$q = "INSERT INTO CommentNotify (PkgID, UserID) VALUES ($pid, $uid)";
				db_query($q, $dbh);
			}

			$output .= $pkgname;
		}
		else {
			$q = "DELETE FROM CommentNotify WHERE PkgID = $pid";
			$q .= " AND UserID = $uid";
			db_query($q, $dbh);

			$output .= $pkgname;
		}
	}

	if ($action) {
		$output = __("You have been added to the comment notification list for %s.", $output);
	}
	else {
		$output = __("You have been removed from the comment notification list for %s.", $output);
	}

	return $output;
}

