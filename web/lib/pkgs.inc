<?
include_once("pkgs_po.inc");

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

# display the search form in a boxSoft style
#
function pkg_search_page($L="",$C="",$K="",$SB="",$O=0,$PP=25) {
	# L: PackageLocations.ID
	# C: PackageCategories.ID
	# K: Keywords
	# SB: Sort by
	# O: Row offset
	# PP: Per page
	$locs = pkgLocations();
	$cats = pkgCategories();
	$devs = getDevelopers();
	$tus = getTrustedUsers();
	$dbh = db_connect();

	print "<center>\n";
	print "<table cellspacing='3' class='boxSoft'>\n";
	print "<tr>\n";
	print "  <td class='boxSoftTitle' align='right'>\n";
	print "    <span class='boxSoftTitle'>".__("Search Criteria")."</span>\n";
	print "  </td>\n";
	print "</tr>\n";
	print "<tr>\n";
	print "  <td class='boxSoft'>\n";
	print "<form action='/pkgsearch.php' method='post'>\n";
	print "<input type='hidden' name='Action' value='SearchPkgs'>\n";
	print "<table style='width: 100%' align='center'>\n";

	print "<tr>\n";
	print "<td align='right'>\n";
	print "  <span class='f5'><span class='blue'>".__("Location");
	print "</span></span><br />\n";
	print "  <select name='L'>\n";
	print "  <option value=0> ".__("Any")."\n";
	while (list($id, $loc) = each($locs)) {
		if ($L == $id) {
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
		if ($C == $id) {
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
	print " value='".$K."' maxlength='35'>\n";
	print "</td>\n";

	print "<td align='right'>\n";
	print "  <span class='f5'><span class='blue'>".__("Sort by");
	print "</span></span><br />\n";
	print "  <select name='SB'>\n";
	print "  <option value=n";
	$SB == "n" ? print "selected> " : print "> ";
	print __("Name")."\n";
	print "  <option value=c";
	$SB == "c" ? print "selected> " : print "> ";
	print __("Category")."\n";
	print "  <option value=l";
	$SB == "l" ? print "selected> " : print "> ";
	print __("Location")."\n";
	print "  <option value=p";
	$SB == "p" ? print "selected> " : print "> ";
	print __("Votes")."\n";
	print "  </select>\n";
	print "</td>\n";

	print "<td align='right'>\n";
	print "  <span class='f5'><span class='blue'>".__("Per page");
	print "</span></span><br />\n";
	print "  <select name='PP'>\n";
	print "  <option value=25";
	$PP == 25 ? print "selected> 25\n" : print "> 25\n";
	print "  <option value=50";
	$PP == 50 ? print "selected> 50\n" : print "> 50\n";
	print "  <option value=75";
	$PP == 75 ? print "selected> 75\n" : print "> 75\n";
	print "  <option value=100";
	$PP == 100 ? print "selected> 100\n" : print "> 100\n";
	print "  </select>\n";
	print "</td>\n";

	print "<td align='right' valign='bottom'>&nbsp;\n";
	print "  <input type='submit' class='button' value='Go'>\n";
	print "</td>\n";

	print "</tr>\n";
	print "</table>\n";

	print "</form>\n";
	print "  </td>\n";
	print "</tr>\n";
	print "</table>\n";
	print "</center>\n";
	print "<br />\n";

	# query to pull out package info
	#
	$q = "SELECT Packages.*, IF(ISNULL(PackageID), 0, COUNT(*)) AS Votes ";
	$q.= "FROM Packages LEFT JOIN PackageVotes ";
	$q.= "ON Packages.ID = PackageVotes.PackageID ";
	$has_where = 0;
	if ($L) {
		$q.= "WHERE LocationID = ".intval($L)." ";
		$has_where = 1;
	}
	if ($C) {
		if (!$has_where) {
			$q.= "WHERE CategoryID = ".intval($C)." ";
			$has_where = 1;
		} else {
			$q.= "AND CategoryID = ".intval($C)." ";
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

	$q.= "GROUP BY PackageID ";
	switch ($SB) {
		case 'c':
			$q.= "ORDER BY CategoryID ASC, Name ASC, LocationID ASC ";
			break;
		case 'l':
			$q.= "ORDER BY LocationID ASC, Name ASC, CategoryID ASC ";
			break;
		default:
			$q.= "ORDER BY Name ASC, LocationID ASC, CategoryID ASC ";
			break;
	}
	$q.= "LIMIT ".intval($O).", ".intval($PP);
	$result = db_query($q, $dbh);
	if (!$result) {
		print $q."<br />\n";
		print __("No packages matched your search criteria.");
	} else {

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
		print "</tr>\n";

		for ($i=0; $row = mysql_fetch_assoc($result); $i++) {
			(($i % 2) == 0) ? $c = "data1" : $c = "data2";
			print "<tr>\n";
			print "  <td class='".$c."'><span class='f5'><span class='blue'>";
			print $locs[$row["LocationID"]]."</span></span></td>\n";
			print "  <td class='".$c."'><span class='f5'><span class='blue'>";
			print $cats[$row["CategoryID"]]."</span></span></td>\n";
			print "  <td class='".$c."'><span class='f4'><span class='blue'>";
			print $row["Name"]."-".$row["Version"]."</span></span></td>\n";
			print "  <td class='".$c."'><span class='f5'><span class='blue'>";
			print "&nbsp;&nbsp;&nbsp;".$row["Votes"]."</span></span></td>\n";
			print "  <td class='".$c."'><span class='f4'><span class='blue'>";
			print $row["Description"]."</span></span></td>\n";
			print "  <td class='".$c."'><span class='f5'><span class='blue'>";
			if (isset($devs[$row["MaintainerUID"]])) {
				print $devs[$row["MaintainerUID"]]["Username"];
			} elseif (isset($tus[$row["MaintainerUID"]])) {
				print $tus[$row["MaintainerUID"]]["Username"];
			} else {
				print "None";
			}
			print "</span></span></td>\n";

			print "</tr>\n";

		}
		print "</table>\n";

		print "  </td>\n";
		print "</tr>\n";
		print "</table>\n";
		print "</center>\n";
	}

	return;
}

# vim: ts=2 sw=2 noet ft=php
?>
