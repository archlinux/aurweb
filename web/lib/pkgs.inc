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
function pkg_search_page($L="",$C="",$K="",$SB="",$PP="") {
	# L: PackageLocations.ID
	# C: PackageCategories.ID
	# K: Keywords
	# SB: Sort by
	# PP: Per page
	$locs = pkgLocations();
	$cats = pkgCategories();

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
	print "</span></span><br>\n";
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
	print "</span></span><br>\n";
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
	print "</span></span><br>\n";
	print "  <input type='text' name='K' size='35'";
	print " value='".$K."' maxlength='35'>\n";
	print "</td>\n";

	print "<td align='right'>\n";
	print "  <span class='f5'><span class='blue'>".__("Sort by");
	print "</span></span><br>\n";
	print "  <select name='SB'>\n";
	print "  <option value=c";
	$SB == "c" ? print "selected> " : print "> ";
	print __("Category")."\n";
	print "  <option value=l";
	$SB == "l" ? print "selected> " : print "> ";
	print __("Location")."\n";
	print "  <option value=m";
	$SB == "m" ? print "selected> " : print "> ";
	print __("Maintainer")."\n";
	print "  <option value=n";
	$SB == "n" ? print "selected> " : print "> ";
	print __("Name")."\n";
	print "  <option value=p";
	$SB == "p" ? print "selected> " : print "> ";
	print __("Popularity")."\n";
	print "  </select>\n";
	print "</td>\n";

	print "<td align='right'>\n";
	print "  <span class='f5'><span class='blue'>".__("Per page");
	print "</span></span><br>\n";
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
	return;
}

# vim: ts=2 sw=2 noet ft=php
?>
