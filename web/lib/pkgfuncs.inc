<?
include_once("pkgfuncs_po.inc");

# grab the current list of PackageCategories
#
function pkgCategories() {
	$cats = array();
	$dbh = db_connect();
	$q = "SELECT * FROM PackageCategories ";
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
	$q = "SELECT * FROM PackageLocations ";
	$q.= "ORDER BY Location ASC";
	$result = db_query($q, $dbh);
	if ($result) {
		while ($row = mysql_fetch_row($result)) {
			$locs[$row[0]] = $row[1];
		}
	}
	return $locs;
}

# grab package dependencies
#
function package_dependencies($pkgid=0) {
	$deps = array();
	if ($pkgid) {
		$dbh = db_connect();
		$q = "SELECT DepPkgID, Name FROM PackageDepends, Packages ";
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

# display package details
#
function package_details($id=0) {
	$q = "SELECT *,Location,Category ";
	$q.= "FROM Packages,PackageLocations,PackageCategories ";
 	$q.= "WHERE Packages.LocationID = PackageLocations.ID ";
	$q.= "AND Packages.CategoryID = PackageCategories.ID ";
	$q.= "ANd Packages.ID = ".intval($_REQUEST["ID"]);
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
			print "<span class='f3'>Package Details</span></td>\n";
			print "</tr>\n";
			print "<tr>\n";
			print "  <td class='boxSoft'>\n";
			print "<center>\n";
			print "<table>\n";
			print "<tr>\n";
			print "  <td colspan='2'><span class='f2'>";
			print $row["Name"] . "-" . $row["Version"]."</span></td>\n";
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
			print $row["Location"]." :: ".$row["Category"]."</span></td>";
			print "</tr>\n";
			print "<tr>\n";
			print "  <td colspan='2'><span class='f3'>".__("Maintainer").": ";
			if (isset($row["AURMaintainerUID"])) {
				$maintainer = username_from_id($row["AURMaintainerUID"]);
			} elseif (isset($row["MaintainerUID"])) {
				$maintainer = username_from_id($row["MaintainerUID"]);
			} else {
				$maintainer = "None";
			}
			print $maintainer . "</span></td>";
			print "</tr>\n";
			print "<tr>\n";
			print "  <td colspan='2'><img src='/images/pad.gif' height='30'></td>";
			print "</tr>\n";
			print "<tr>\n";
			print "  <td valign='top' style='padding-right: 10'>";
			print "<table class='boxSoft' style='width: 200px'>";
			print "<tr><td class='boxSoftTitle'><span class='f3'>";
			print "Dependencies</span></td></tr>\n";
			print "<tr><td class='boxSoft'>";
			$deps = package_dependencies($row["ID"]); # $deps[0] = array('id','name');
			while (list($k, $darr) = each($deps)) {
				print $darr[0]." - ".$darr[1]."<br />\n";
			}
			print "</td></tr>\n";
			print "</table></td>";

			print "  <td valign='top'>";
			print "<table class='boxSoft' style='width: 200px'>";
			print "<tr><td class='boxSoftTitle'><span class='f3'>";
			print "Sources</span></td></tr>\n";
			print "<tr><td class='boxSoft'>";
			$sources = package_sources($row["ID"]); # $sources[0] = 'src';
			while (list($k, $src) = each($sources)) {
				# TODO left off here... URLify
				print $src."<br />\n";
			}
			print "</td></tr>\n";
			print "</table></td>";

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
	$dbh = db_connect();


	# determine paging variables
	#
	isset($_REQUEST["PP"]) ? $PP = intval($_REQUEST["PP"]) : $PP = 25;
	if ($PP < 25) {$PP = 25;}
	if ($PP > 100) {$PP = 100;}
	isset($_REQUEST["O"]) ? $O = intval($_REQUEST["O"]) : $O = 0;
	if (isset($_REQUEST["do_More"])) {
		$O += $PP;
	} elseif (isset($_REQUEST["do_Less"])) {
		$O -= $PP;
	}
	if ($O < 0) {
		$O = 0;
	}
	if (isset($_REQUEST["do_Search"]) || isset($_REQUEST["do_MyPackages"])) {
		# reset the offset to zero if they hit Go/My Packages
		#
		$O = 0;
	}


	# grab info for user if they're logged in
	#
	if ($SID) {
		$myuid = uid_from_sid($SID);
		$acct = account_from_sid($SID);
	}

	# The search form
	#
	print "<form action='/pkgsearch.php' method='post'>\n";
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
	$has_where = 0;
	if (isset($_REQUEST["L"]) && intval($_REQUEST["L"])) {
		$q.= "WHERE LocationID = ".intval($_REQUEST["L"])." ";
		$has_where = 1;
	}
	if (isset($_REQUEST["C"]) && intval($_REQUEST["C"])) {
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
	if (isset($_REQUEST["do_MyPackages"]) && $SID) {
		# list packages that the user is a AUR Maintainer of, or if it the
		# vistior is a registered user, if they are the Maintainer.
		#
		if ($myuid) {
			if (!$has_where) {
				$q.= "WHERE (AURMaintainerUID = ".$myuid." OR ";
				$q.= "MaintainerUID = " . $myuid.") ";
				$has_where = 1;
			} else {
				$q.= "AND (AURMaintainerUID = ".$myuid." OR ";
				$q.= "MaintainerUID = " . $myuid.") ";
			}
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
	$q.= "LIMIT ".$O.", ".$PP;
	print $q."<br />\n";
	print "<pre>\n";
	print_r($_REQUEST);
	print "</pre>\n";

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
			print "<input type='submit' class='button' name='do_Adopt'";
			print "	value='".__("Adopt Packages")."'></td>\n";
			print "  <td align='center'>";
			print "<input type='submit' class='button' name='do_Disown'";
			print "	value='".__("Disown Packages")."'></td>\n";
			print "  <td align='center'>";
			print "<input type='submit' class='button' name='do_Vote'";
			print "	value='".__("Vote")."'></td>\n";
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
		print "  <th style='border-bottom: #666 1px solid; vertical-align:";
		print " bottom'><span class='f2'>".__("Description")."</span></th>\n";
		print "  <th style='border-bottom: #666 1px solid; vertical-align:";
		print " bottom'><span class='f2'>".__("Maintainer")."</span></th>\n";
		if ($SID) {
			print "  <th style='border-bottom: #666 1px solid; vertical-align:";
			print " bottom'><span class='f2'>".__("Manage")."</span></th>\n";
		}
		print "</tr>\n";

		for ($i=0; $row = mysql_fetch_assoc($result); $i++) {
			(($i % 2) == 0) ? $c = "data1" : $c = "data2";
			print "<tr>\n";
			if ($SID) {
				print "  <td class='".$c."'>";
				if ($row["OutOfDate"]) {
					print "<span style='background-color: red'>";
				}
				print "<input type='checkbox' name='IDs[]' value='".$row["ID"]."'>";
				if ($i == 0) {
					$all_ids = $row["ID"];
				} else {
					$all_ids .= ":".$row["ID"];
				}
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
			$details_url = "<a href='/pkgsearch.php?";
			$url_data = "do_Details=1&ID=";
			$url_data.= $row["ID"];
			while (list($k, $var) = each($pkgsearch_vars)) {
				# I'm never convinced how to do this encoding/decoding properly.
				# php.net recommends htmlentities(urlencode(data)), but that
				# doesn't work!
				#
				$url_data .= "&".$var."=".rawurlencode(stripslashes($_REQUEST[$var]));
			}
			$details_url.= $url_data;
			$details_url.= "'><span class='black'>".$row["Name"];
			$details_url.= "-".$row["Version"]."</span></a>";
			print $details_url."</span></td>\n";
			print "  <td class='".$c."'><span class='f5'><span class='blue'>";
			print "&nbsp;&nbsp;&nbsp;".$row["NumVotes"]."</span></span></td>\n";
			print "  <td class='".$c."'><span class='f4'><span class='blue'>";
			print $row["Description"]."</span></span></td>\n";
			print "  <td class='".$c."'><span class='f5'><span class='blue'>";
			$not_managed = 0;
			if (isset($devs[$row["AURMaintainerUID"]])) {
				print $devs[$row["AURMaintainerUID"]]["Username"];
			} elseif (isset($tus[$row["AURMaintainerUID"]])) {
				print $tus[$row["AURMaintainerUID"]]["Username"];
			} else {
				print "None";
				$not_managed = 1;
			}
			print "</span></span></td>\n";
			if ($myuid == $row["AURMaintainerUID"] || $not_managed ||
					($myuid == $row["MaintainerUID"] && $not_managed)) {
				# Only allow TUs/Devs to manage packages, or if it is a regular
				# user and the package has not been adopted by a TU/Dev, then the
				# regular user (most likely the submitter) can manage it.
				#
				$manage_url = "<a href='/pkgmgmnt.php?ID=";
				$manage_url.= $row["ID"]."'><span class='black'>Manage</span></a>";
				print "  <td class='".$c."'><span class='f4'>";
				print $manage_url."</span></td>\n";
			} else {
				print "<td class='".$c."'><span class='f4'>&nbsp;</span></td>\n";
			}

			print "</tr>\n";

		}
		print "</table>\n";
		print "  </td>\n";
		print "</tr>\n";
		print "</table>\n";
		print "<input type='hidden' name='All_IDs' value='".$all_ids."'>\n";

		print "<table width='90%' cellspacing='0' cellpadding='2'>\n";
		print "<tr>\n";
		print "  <td>\n";
		print "  <table border='0' cellpadding='0' cellspacing='0' width='100%'>\n";
		print "  <tr>\n";
		print "    <td align='left'>";
		print "    <input type='submit' class='button' name='do_Less'";
		print " value='&lt;-- ".__("Less")."'>\n";
		print "    </td>\n";
		print "    <td align='right'>";
		print "    <input type='submit' class='button' name='do_More'";
		print " value='".__("More")." --&gt;'>\n";
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
