<?
include_once("pkgfuncs_po.inc");

# define variables used during pkgsearch
#
$pkgsearch_vars = array("O", "L", "C", "K", "SB", "PP", "do_MyPackages");


# print out the 'return to package details' link
#
function pkgdetails_link($id=0) {
	$url_data = "<a href='/packages.php?do_Details=1&ID=".intval($id)."'>";
	print __("Go back to %hpackage details view%h.",
		array($url_data, "</a>"));
	print "\n<br />\n";
	return;
}


# print out the 'return to search results' link
#
function pkgsearch_results_link() {
	global $_REQUEST;
	global $pkgsearch_vars;

	$url_data = "<a href='/packages.php?do_Search=1";
	while (list($k, $var) = each($pkgsearch_vars)) {
		if ($var == "do_MyPackages" && $_REQUEST[$var]) {
			$url_data.="&".$var."=1";
		} else {
			$url_data.="&".$var."=".rawurlencode(stripslashes($_REQUEST[$var]));
		}
	}
	$url_data .= "'>";
	print __("Go back to %hsearch results%h.",
		array($url_data, "</a>"));
	print "\n<br />\n";

	return;
}

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
	$q = "SELECT * FROM PackageLocations WHERE ID != 1 ";
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
	$q.= "WHERE Name = '".mysql_escape_string($name)."' ";
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
		$q = "SELECT DepPkgID, Name, DummyPkg FROM PackageDepends, Packages ";
		$q.= "WHERE PackageDepends.DepPkgID = Packages.ID ";
		$q.= "AND PackageDepends.PackageID = ".mysql_escape_string($pkgid);
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
		$q.= mysql_escape_string($pname)."'";
		$result = db_query($q, $dbh);
		if (!mysql_num_rows($result)) {
			# Insert the dummy
			#
			$q = "INSERT INTO Packages (Name, Description, URL, SubmittedTS, ";
			$q.= "SubmitterUID, DummyPkg) VALUES ('";
			$q.= mysql_escape_string($pname)."', 'A dummy package', '/#', ";
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
		$q = "SELECT PackageComments.ID, UserName, Comments, CommentTS ";
		$q.= "FROM PackageComments, Users ";
		$q.= "WHERE PackageComments.UsersID = Users.ID";
		$q.= " AND PackageID = ".mysql_escape_string($pkgid);
		$q.= " AND DelUsersID = 0"; # only display non-deleted comments
		$q.= " ORDER BY CommentTS ASC";
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
		$q.= "WHERE PackageID = ".mysql_escape_string($pkgid);
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
	$q.= "AND Sessions.SessionID = '".mysql_escape_string($sid)."'";
	$result = db_query($q, $dbh);
	if ($result) {
		while ($row = mysql_fetch_row($result)) {
			$pkgs[$row[0]] = 1;
		}
	}
	return $pkgs;
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
			print "<br />\n";
			print "<center>\n";
			print "<table cellspacing='3' class='boxSoft'>\n";
			print "<tr>\n";
			print "  <td class='boxSoftTitle' align='right'>";
			print "<span class='f3'>".__("Package Details")."</span></td>\n";
			print "</tr>\n";
			print "<tr>\n";
			print "  <td class='boxSoft'>\n";
			print "<center>\n";
			print "<table>\n";
			print "<tr>\n";
			print "  <td colspan='2'><span class='f2'>";
			print $row["Name"] . " " . $row["Version"]."</span></td>\n";
			print "</tr>\n";
			print "<tr>\n";
			print "  <td colspan='2'><span class='f3'>";
			print "<a href='".$row["URL"]."'>".$row["URL"]."</a></span></td>\n";
			print "</tr>\n";
			print "<tr>\n";
			print "  <td colspan='2'><span class='f3'>".$row["Description"];
			print "</a></span></td>\n";
			print "</tr>\n";
			print "<tr>\n";
			print "  <td colspan='2'><img src='/images/pad.gif' height='30'></td>";
			print "</tr>\n";
			print "<tr>\n";
			print "  <td colspan='2'><span class='f3'>";
			if ($row["Location"] == "unsupported") {
			  $edit_cat = "<a href='/pkgedit.php?change_Category=1&ID=";
			  $edit_cat .= intval($_REQUEST["ID"])."'>".$row["Category"]."</a>";
			  $edit_cat .= " &nbsp;<span class='fix'>(";
			  $edit_cat .= __("change category").")</span>";
			} else {
				$edit_cat = $row["Category"];
			}
			print $row["Location"]." :: ".$edit_cat."</span></td>";

			print "</tr>\n";
			print "<tr>\n";
			print "  <td colspan='2'><span class='f3'>".__("Maintainer").": ";
			if ($row["AURMaintainerUID"]) {
				$maintainer = username_from_id($row["AURMaintainerUID"]);
			} elseif ($row["MaintainerUID"]) {
				$maintainer = username_from_id($row["MaintainerUID"]);
			} else {
				$maintainer = "None";
			}
			print $maintainer . "</span></td>";
			print "</tr>\n";
			print "<tr>\n";
			print "  <td colspan='2'><img src='/images/pad.gif' height='15'></td>";
			print "</tr>\n";
			print "<tr>\n";
			print "  <td colspan='2'><span class='f3'>";
			if ($row["LocationID"] == 2) {
			  print "<a href='".$row['URLPath']."'>Tarball</a> :: <a href='".dirname($row['URLPath'])."/".$row['Name']."'>Files</a></span></td>";
			} elseif ($row["LocationID"] == 3) {
			  print "<a href='http://cvs.archlinux.org/cgi-bin/viewcvs.cgi/" . $row["Category"] . "/" . $row["Name"] . "/?cvsroot=AUR&only_with_tag=CURRENT'>CVS</td>";
			}
			print "</tr>\n";
			print "<tr>\n";
			print "  <td colspan='2'><img src='/images/pad.gif' height='30'></td>";
			print "</tr>\n";
			print "<tr>\n";
			print "  <td valign='top' style='padding-right: 10'>";
			print "<table class='boxSoft' style='width: 200px'>";
			print "<tr><td class='boxSoftTitle'><span class='f3'>";
			print __("Dependencies")."</span></td></tr>\n";
			print "<tr><td class='boxSoft'>";
			$deps = package_dependencies($row["ID"]); # $deps[0] = array('id','name', 'dummy');
			while (list($k, $darr) = each($deps)) {
				$url = "<a href='/packages.php?do_Details=1&ID=".$darr[0];
				while(list($k, $var) = each($pkgsearch_vars)) {
					if ($var == "do_MyPackages" && $_REQUEST[$var]) {
						$url .= "&".$var."=1";
					} else {
						$url .= "&".$var."=".rawurlencode(stripslashes($_REQUEST[$var]));
					}
				}
				reset($pkgsearch_vars);
				if ($darr[2] == 0) print $url."'>".$darr[1]."</a><br />\n";
				else print "<a href='#'>".$darr[1]."</a><br />\n";
			}
			print "</td></tr>\n";
			print "</table></td>";

			print "  <td valign='top'>";
			print "<table class='boxSoft' style='width: 200px'>";
			print "<tr><td class='boxSoftTitle'><span class='f3'>";
			print __("Sources")."</span></td></tr>\n";
			print "<tr><td class='boxSoft'>";
			$sources = package_sources($row["ID"]); # $sources[0] = 'src';
			while (list($k, $src) = each($sources)) {
				$parsed_url = parse_url($src);
				if ($parsed_url['scheme'])
				{
					//It is an external source
					print "<a href='".$src."'>".$src."</a><br />\n";
				}
				else 
				{
					//It is presumably an internal source
					if ($row["LocationID"] == 2) {
						print "<a href='".dirname($row['URLPath'])."/".$row['Name'];
						print "/".$src."'>".$src."</a><br />\n";
					} elseif ($row["LocationID"] == 3) {
						print "<a href='http://cvs.archlinux.org/cgi-bin/viewcvs.cgi/*checkout*/".$row["Category"]."/".$row["Name"]."/".$src."/?rev=HEAD&cvsroot=AUR&only_with_tag=CURRENT'>";
						print $src."</a><br />\n";
					}
				}
			}
			print "</td></tr>\n";
			print "</table></td>";
			print "</tr>\n";

			# Display package comments
			#
			$comments = package_comments($row["ID"]);
			if (!empty($comments)) {
				while (list($indx, $carr) = each($comments)) {
					print "<tr>\n";
					print "  <td colspan='2'>";
					print "<img src='/images/pad.gif' height='2'></td></tr>\n";

					print "<tr>\n";
					print "  <td valign='top' style='padding-right: 10' colspan='2'>";
					print "<table class='boxSoft' width='100%'>";
					print "<tr><td class='boxSoftTitle'><span class='f3'>";
					if (canDeleteComment($carr["ID"], account_from_sid($SID), $SID)) {
						$durl = "<a href='/pkgedit.php?del_Comment=1";
						$durl.= "&comment_id=".$carr["ID"]."&ID=".$row["ID"];
						$durl.= "'><img src='/images/x.png' border='0'";
						$durl.= " alt=\"".__("Delete comment")."\"></a>";
					}
					print $durl . "&nbsp;&nbsp;";
					print __("Comment by: %h%s%h on %h%s%h",
							array("<b>",$carr["UserName"],"</b>",
							      "<i>",date("Ymd [H:i:s]",$carr["CommentTS"]),"</i>"));
					print "</span>";
					print "<tr><td class='boxSoft'>";
					print "<code>\n";
					print str_replace("\n", "<br>", str_replace('"',"&quot;", htmlspecialchars(strip_tags(stripslashes($carr["Comments"])))));
					print "</code>\n";
					print "</td></tr>\n";
					print "</table>\n";
					print "  </td>\n";
					print "</tr>\n";
				}
			}

			print "<tr>\n";
			print "  <td colspan='2'><img src='/images/pad.gif' height='2'>";
			print "</td></tr>\n";
			print "<tr>\n";
			print "  <td colspan='2'>";
			print "<form action='/pkgedit.php' method='post'>\n";
			print "<input type='hidden' name='ID' value='".$row["ID"]."'>\n";
			print "<input type='submit' class='button' name='add_Comment' value=\"";
			print __("Add Comment")."\">";
			print "</form>\n";
			print "  </td>";
			if ($SID) {
				print "<td><form action='/packages.php' method='post'>\n";
				print "<input type='hidden' name='IDs[".$row["ID"]."]' value='1'>\n";
				print "<input type='hidden' name='ID' value='".$row["ID"]."'>\n";
				$q = "SELECT * FROM PackageVotes WHERE UsersID = ".uid_from_sid($SID);
				$q.= " AND PackageID = ".$row["ID"];
				if (!mysql_num_rows(db_query($q, $dbh))) {
					print "<input type='submit' class='button' name='do_Vote'";
					print " value='".__("Vote")."'>";
				} else {
					print "<input type='submit' class='button' name='do_UnVote'";
					print " value='".__("Un-Vote")."'>";
				}
				print "</form></td>\n";
			}
			print "</tr>\n";

			print "</table>\n";
			print "</center>\n";
			print "  </td>\n";
			print "</tr>\n";

			print "</table>\n";
		}
	}
	return;
}


# display the search form in a boxSoft style
#
function pkg_search_page($SID="") {
	global $_REQUEST;
	global $pkgsearch_vars;
	# SID: session id cookie

	$locs = pkgLocations();
	$cats = pkgCategories();
	$devs = getDevelopers();
	$tus = getTrustedUsers();
	$users = getUsers();
	$dbh = db_connect();


	# determine paging variables
	#
	$_REQUEST["PP"] ? $PP = intval($_REQUEST["PP"]) : $PP = 25;
	if ($PP < 25) {$PP = 25;}
	if ($PP > 100) {$PP = 100;}
	$_REQUEST["O"] ? $O = intval($_REQUEST["O"]) : $O = 0;
	if ($_REQUEST["do_More"]) {
		$O += $PP;
	} elseif ($_REQUEST["do_Less"]) {
		$O -= $PP;
	}
	if ($O < 0) {
		$O = 0;
	}
	if ($_REQUEST["do_Search"] && $_REQUEST["do_Search"] != 1) {
		# reset the offset to zero if they hit Go
		#
		$_REQUEST["do_MyPackages"] = 0;
		$O = 0;
	}
	$_REQUEST["O"] = $O; # so that pkg_search_results() works


	# grab info for user if they're logged in
	#
	if ($SID) {
		$myuid = uid_from_sid($SID);
		$acct = account_from_sid($SID);
		$my_votes = pkgvotes_from_sid($SID);
	}

	# The search form
	#
	print "<form action='/packages.php' method='post'>\n";
	print "<input type='hidden' name='O' value='".$O."'>\n";

	print "<center>\n";
	print "<table cellspacing='3' class='boxSoft'>\n";
	print "<tr>\n";
	print "  <td class='boxSoftTitle' align='right'>\n";
	print "    <span class='f3'>".__("Search Criteria")."</span>\n";
	print "  </td>\n";
	print "</tr>\n";
	print "<tr>\n";
	print "  <td class='boxSoft'>\n";
	print "<table style='width: 100%' align='center'>\n";

	print "<tr>\n";
	print "<td align='right'>\n";
	print "  <span class='f5'><span class='blue'>".__("Location");
	print "</span></span><br />\n";
	print "  <select name='L'>\n";
	print "  <option value=0> ".__("Any")."\n";
	while (list($id, $loc) = each($locs)) {
		if (intval($_REQUEST["L"]) == $id) {
			print "  <option value=".$id." selected> ".$loc."\n";
		} else {
			print "  <option value=".$id."> ".$loc."\n";
		}
	}
	print "  </select>\n";
	print "</td>\n";

	print "<td align='right'>\n";
	print "  <span class='f5'><span class='blue'>".__("Category");
	print "</span></span><br />\n";
	print "  <select name='C'>\n";
	print "  <option value=0> ".__("Any")."\n";
	while (list($id, $cat) = each($cats)) {
		if (intval($_REQUEST["C"]) == $id) {
			print "  <option value=".$id." selected> ".$cat."\n";
		} else {
			print "  <option value=".$id."> ".$cat."\n";
		}
	}
	print "  </select>\n";
	print "</td>\n";

	print "<td align='right'>\n";
	print "  <span class='f5'><span class='blue'>".__("Keywords");
	print "</span></span><br />\n";
	print "  <input type='text' name='K' size='35'";
	$K = str_replace("\"", "", $_REQUEST["K"]); # TODO better testing for
                                              # SQL trickery...
	print " value=\"".stripslashes($K)."\" maxlength='35'>\n";
	print "</td>\n";

	print "<td align='right'>\n";
	print "  <span class='f5'><span class='blue'>".__("Sort by");
	print "</span></span><br />\n";
	print "  <select name='SB'>\n";
	print "  <option value=n";
	$_REQUEST["SB"] == "n" ? print " selected> " : print "> ";
	print __("Name")."\n";
	print "  <option value=c";
	$_REQUEST["SB"] == "c" ? print " selected> " : print "> ";
	print __("Category")."\n";
	print "  <option value=l";
	$_REQUEST["SB"] == "l" ? print " selected> " : print "> ";
	print __("Location")."\n";
	print "  <option value=v";
	$_REQUEST["SB"] == "v" ? print " selected> " : print "> ";
	print __("Votes")."\n";
	print "  </select>\n";
	print "</td>\n";

	print "<td align='right'>\n";
	print "  <span class='f5'><span class='blue'>".__("Per page");
	print "</span></span><br />\n";
	print "  <select name='PP'>\n";
	print "  <option value=25";
	$PP == 25 ? print " selected> 25\n" : print "> 25\n";
	print "  <option value=50";
	$PP == 50 ? print " selected> 50\n" : print "> 50\n";
	print "  <option value=75";
	$PP == 75 ? print " selected> 75\n" : print "> 75\n";
	print "  <option value=100";
	$PP == 100 ? print " selected> 100\n" : print "> 100\n";
	print "  </select>\n";
	print "</td>\n";

	print "<td align='right' valign='bottom'>&nbsp;\n";
	print "  <input type='submit' class='button' name='do_Search'";
	print " value='".__("Go")."'>\n";
	print "</td>\n";

	if ($SID) {
		print "<td align='right' valign='bottom'>&nbsp;\n";
		print "  <input type='submit' class='button' name='do_MyPackages'";
	 	print "	value='".__("My Packages")."'>\n";
		print "</td>\n";
	}

	print "<td align='right' valign='bottom'>&nbsp;\n";
	print "  <input type='submit' class='button' name='do_Orphans'";
	print " value='".__("Orphans")."'>\n";
	print "</td>\n";

	print "</tr>\n";
	print "</table>\n";

	print "  </td>\n";
	print "</tr>\n";
	print "</table>\n";
	print "</center>\n";
	print "<br />\n";

	# query to pull out package info
	#
#	$q = "SELECT Packages.*, IF(ISNULL(PackageID), 0, COUNT(*)) AS Votes ";
#	$q.= "FROM Packages LEFT JOIN PackageVotes ";
#	$q.= "ON Packages.ID = PackageVotes.PackageID ";
	$q = "SELECT * FROM Packages ";
	$q.= "WHERE DummyPkg != 1 ";
	$has_where = 1;

	if (intval($_REQUEST["L"])) {
		if (!$has_where) {
		  $q.= "WHERE LocationID = ".intval($_REQUEST["L"])." ";
		} else {
			$q .= "AND LocationID = ".intval($_REQUEST["L"])." ";
		}
		$has_where = 1;
	}
	if (intval($_REQUEST["C"])) {
		if (!$has_where) {
			$q.= "WHERE CategoryID = ".intval($_REQUEST["C"])." ";
			$has_where = 1;
		} else {
			$q.= "AND CategoryID = ".intval($_REQUEST["C"])." ";
		}
	}
	if ($K) {
		if (!$has_where) {
			$q.= "WHERE (Name LIKE '".mysql_escape_string($K)."%' OR ";
			$q.= "Description LIKE '%".mysql_escape_string($K)."%') ";
			$has_where = 1;
		} else {
			$q.= "AND (Name LIKE '".mysql_escape_string($K)."%' OR ";
			$q.= "Description LIKE '%".mysql_escape_string($K)."%') ";
		}
	}
	if ($_REQUEST["do_MyPackages"] && $SID) {
		# list packages that the user is a AUR Maintainer of, or if it the
		# vistior is a registered user, if they are the Maintainer.
		#
		if ($myuid) {
			if (!$has_where) {
				$q.= "WHERE (AURMaintainerUID = ".$myuid." OR ";
				$q.= "MaintainerUID = ".$myuid." OR SubmitterUID = ".$myuid.") ";
				$has_where = 1;
			} else {
				$q.= "AND (AURMaintainerUID = ".$myuid." OR ";
				$q.= "MaintainerUID = ".$myuid." OR SubmitterUID = ".$myuid.") ";
			}
		}
	}
	if ($_REQUEST["do_Orphans"]) {
		# List packages that have neither a Maintainer nor AURMaintainer
		#
			if (!$has_where) {
				$q.= "WHERE (AURMaintainerUID = 0 AND ";
				$q.= "MaintainerUID = 0) ";
				$has_where = 1;
			} else {
				$q.= "AND (AURMaintainerUID = 0 AND ";
				$q.= "MaintainerUID = 0) ";
			}
	}
	switch ($_REQUEST["SB"]) {
		case 'c':
			$q.= "ORDER BY CategoryID DESC, Name ASC, LocationID ASC ";
			break;
		case 'l':
			$q.= "ORDER BY LocationID ASC, Name ASC, CategoryID DESC ";
			break;
		case 'v':
			$q.= "ORDER BY NumVotes DESC, Name ASC, CategoryID DESC ";
			break;
		default:
			$q.= "ORDER BY Name ASC, LocationID ASC, CategoryID DESC ";
			break;
	}
	$qnext = $q."LIMIT ".($O+$PP).", ".$PP; //next page's worth
	$q.= "LIMIT ".$O.", ".$PP;

	$result = db_query($q, $dbh);
	if (!$result) {
		print __("Error retrieving package list.");

	} elseif (!mysql_num_rows($result)) {
		print __("No packages matched your search criteria.");

	} else {

		if ($SID) {
			# The 'Actions' table
			#
			print "<center>\n";
			print "<table cellspacing='3' class='boxSoft'>\n";
			print "<tr>\n";
			print "  <td class='boxSoftTitle' align='right'>\n";
			print "    <span class='f3'>".__("Actions")."</span>\n";
			print "  </td>\n";
			print "</tr>\n";
			print "<tr>\n";
			print "  <td class='boxSoft'>\n";
			print "<table style='width: 100%' align='center'>\n";
			print "<tr>\n";
			print "  <td align='center'>";
			print "<input type='submit' class='button' name='do_Flag'";
			print "	value='".__("Flag Out-of-date")."'></td>\n";
			print "  <td align='center'>";
			print "<input type='submit' class='button' name='do_UnFlag'";
			print "	value='".__("Unflag Out-of-date")."'></td>\n";
			print "  <td align='center'>";
			print "<input type='submit' class='button' name='do_Adopt'";
			print "	value='".__("Adopt Packages")."'></td>\n";
			print "  <td align='center'>";
			print "<input type='submit' class='button' name='do_Disown'";
			print "	value='".__("Disown Packages")."'></td>\n";
			print "  <td align='center'>";
			print "<input type='submit' class='button' name='do_Delete'";
			print "	value='".__("Delete Packages")."'></td>\n";
			print "  <td align='center'>";
			print "<input type='submit' class='button' name='do_Vote'";
			print "	value='".__("Vote")."'></td>\n";
			print "  <td align='center'>";
			print "<input type='submit' class='button' name='do_UnVote'";
			print "	value='".__("Un-Vote")."'></td>\n";
			print "</tr>\n";
			print "</table>\n";
			print "  </td>\n";
			print "</tr>\n";
			print "</table>\n";
			print "</center>\n";
			print "<br />\n";
		}

		# print out package search results
		#
		print "<center>\n";
		print "<table cellspacing='3' class='boxSoft'>\n";
		print "<tr>\n";
		print "  <td class='boxSoftTitle' align='right'>\n";
		print "    <span class='f3'>Package Listing</span>\n";
		print "  </td>\n";
		print "</tr>\n";
		print "<tr>\n";
		print "  <td class='boxSoft'>\n";
		print "<table width='100%' cellspacing='0' cellpadding='2'>\n";
		print "<tr>\n";
		if ($SID) {
			print "  <th style='border-bottom: #666 1px solid; vertical-align:";
			print " bottom'>&nbsp;</th>\n";
		}
		print "  <th style='border-bottom: #666 1px solid; vertical-align:";
		print " bottom'><span class='f2'>".__("Location")."</span></th>\n";
		print "  <th style='border-bottom: #666 1px solid; vertical-align:";
		print " bottom'><span class='f2'>".__("Category")."</span></th>\n";
		print "  <th style='border-bottom: #666 1px solid; vertical-align:";
		print " bottom'><span class='f2'>".__("Name")."</span></th>\n";
		print "  <th style='border-bottom: #666 1px solid; vertical-align:";
		print " bottom'><span class='f2'>".__("Votes")."</span></th>\n";
		if ($SID) {
			print "  <th style='border-bottom: #666 1px solid; vertical-align:";
			print " bottom'><span class='f2'>".__("Vote")."</span></th>\n";
		}
		print "  <th style='border-bottom: #666 1px solid; vertical-align:";
		print " bottom'><span class='f2'>".__("Description")."</span></th>\n";
		print "  <th style='border-bottom: #666 1px solid; vertical-align:";
		print " bottom'><span class='f2'>".__("Maintainer")."</span></th>\n";
# REMOVED LINK TO 'pkgmgmnt.php'
#		if ($SID) {
#			print "  <th style='border-bottom: #666 1px solid; vertical-align:";
#			print " bottom'><span class='f2'>".__("Manage")."</span></th>\n";
#		}
		print "</tr>\n";

		for ($i=0; $row = mysql_fetch_assoc($result); $i++) {
			(($i % 2) == 0) ? $c = "data1" : $c = "data2";
			print "<tr>\n";
			if ($SID) {
				print "  <td class='".$c."'>";
				if ($row["OutOfDate"]) {
					print "<span style='background-color: red'>";
				}
				if ($row["MaintainerUID"]==0 && $row["AURMaintainerUID"]==0) {
					print "<span style='background-color: cyan'>";
				}	
				print "<input type='checkbox' name='IDs[".$row["ID"]."]' value='1'>";
#				if ($i == 0) {
#					$all_ids = $row["ID"];
#				} else {
#					$all_ids .= ":".$row["ID"];
#				}
				if ($row["OutOfDate"]) {
					print "</span>";
				}
				print "</td>\n";
			}
			print "  <td class='".$c."'><span class='f5'><span class='blue'>";
			print $locs[$row["LocationID"]]."</span></span></td>\n";
			print "  <td class='".$c."'><span class='f5'><span class='blue'>";
			print $cats[$row["CategoryID"]]."</span></span></td>\n";
			print "  <td class='".$c."'><span class='f4'>";
			$url = "<a href='/packages.php?";
			$url .= "do_Details=1&ID=";
			$url .= $row["ID"];
			while (list($k, $var) = each($pkgsearch_vars)) {
				# I'm never convinced how to do this encoding/decoding properly.
				# php.net recommends htmlentities(urlencode(data)), but that
				# doesn't work!
				#
				if ($var == "do_MyPackages" && $_REQUEST[$var]) {
					$url .= "&".$var."=1";
				} else {
					$url .= "&".$var."=".rawurlencode(stripslashes($_REQUEST[$var]));
				}
			}
			reset($pkgsearch_vars);
			$url.= "'><span class='black'>".$row["Name"];
			$url.= " ".$row["Version"]."</span></a>";
			print $url."</span></td>\n";
			print "  <td class='".$c."'><span class='f5'><span class='blue'>";
			print "&nbsp;&nbsp;&nbsp;".$row["NumVotes"]."</span></span></td>\n";
			if ($SID) {
				print "  <td class='".$c."'><span class='f5'><span class='blue'>";
				if (isset($my_votes[$row["ID"]])) {
					print "&nbsp;&nbsp;".__("Yes")."</span></td>\n";
				} else {
					print "&nbsp;</span></td>\n";
				}
			}
			print "  <td class='".$c."'><span class='f4'><span class='blue'>";
			print $row["Description"]."</span></span></td>\n";
			print "  <td class='".$c."'><span class='f5'><span class='blue'>";

			# print the package manager, also determine if it is managed
			#
			$managed = 1;
			#			if (isset($devs[$row["AURMaintainerUID"]])) {
			#				print $devs[$row["AURMaintainerUID"]]["Username"];
			# } else
			#			if (isset($tus[$row["MaintainerUID"]])) {
			#				print $tus[$row["MaintainerUID"]]["Username"];
			if (isset($users[$row["MaintainerUID"]])) {
				print $users[$row["MaintainerUID"]]["Username"];
			} else {
				print __("None");
				$managed = 0;
			}
			print "</span></span></td>\n";

# REMOVED LINK TO 'pkgmgmnt.php'
#			# print the managed link if applicable
#			#
#			if (canManagePackage($myuid, $row["AURMaintainerUID"],
#					$row["MaintainerUID"], $row["SubmitterUID"], $managed)) {
#				$manage_url = "<a href='/pkgmgmnt.php?ID=";
#				$manage_url.= $row["ID"]."'><span class='black'>Manage</span></a>";
#				print "  <td class='".$c."'><span class='f4'>";
#				print $manage_url."</span></td>\n";
#			} else {
#				print "<td class='".$c."'><span class='f4'>&nbsp;</span></td>\n";
#			}

			print "</tr>\n";

		}
		print "</table>\n";
		print "  </td>\n";
		print "</tr>\n";
		print "</table>\n";
#		print "<input type='hidden' name='All_IDs' value='".$all_ids."'>\n";
		if ($_REQUEST["do_MyPackages"]) {
			print "<input type='hidden' name='do_MyPackages' value='1'>\n";
		}

		print "<table width='90%' cellspacing='0' cellpadding='2'>\n";
		print "<tr>\n";
		print "  <td>\n";
		print "  <table border='0' cellpadding='0' cellspacing='0' width='100%'>\n";
		print "  <tr>\n";
		print "    <td align='left'>";
		if (($O-$PP) >= 0) {
			print "    <input type='submit' class='button' name='do_Less'";
			print " value='&lt;-- ".__("Less")."'>\n";
		}
		print "    </td>\n";
		if ($SID) {
			print "    <td align='center'><span class='f5'>\n";
			print "      <font style='background-color: cyan'>O</font>rphan&nbsp;&nbsp;&nbsp;&nbsp;\n";
			print "      <font style='background-color: red'>O</font>ut-of-Date\n";
			print "    </span></td>\n";
		}
		print "    <td align='right'>";
		if (mysql_num_rows(db_query($qnext, $dbh))) {
			print "    <input type='submit' class='button' name='do_More'";
			print " value='".__("More")." --&gt;'>\n";
		}
		print "    </td>\n";
		print "  </tr>\n";
		print "  </table>\n";
		print "  </td>\n";
		print "</tr>\n";
		print "</table>\n";
		print "</center>\n";
	}
	print "</form>\n";

	return;
}

# vim: ts=2 sw=2 noet ft=php
?>
