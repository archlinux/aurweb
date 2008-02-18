<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../lang');

# include("index_po.inc");
include("pkgfuncs_po.inc"); # Add to handle the i18n of My Packages
include("aur.inc");
set_lang();
check_sid();
html_header(__("Home"));

# Big Top Level Table (Table 1)
echo "<div class=\"pgbox\">\n";
echo "  <div class=\"pgboxtitle\"><span class=\"f3\">AUR ".__("Home")."</span></div>\n";
echo "  <div class=\"frontpgboxbody\">\n";
echo "<table border='0' cellpadding='0' cellspacing='3' width='90%'>\n";

# MAIN: Top
echo "<tr>\n";
print "<td class='boxSoft' valign='top' colspan='2'>";
print "<p>".__("Welcome to the AUR! Please read the %hAUR User Guidelines%h and %hAUR TU Guidelines%h for more information.", array('<a href="http://wiki.archlinux.org/index.php/AUR_User_Guidelines">', '</a>', '<a href="http://wiki.archlinux.org/index.php/AUR_Trusted_User_Guidelines">', '</a>'))."<br>";
print __("Contributed PKGBUILDs <b>must</b> conform to the %hArch Packaging Standards%h otherwise they will be deleted!", array('<a href="http://wiki.archlinux.org/index.php/Arch_Packaging_Standards">', '</a>'))."</p>";
print "<p>".__("Remember to vote for your favourite packages!")."<br>";
print __("The most popular packages will be provided as binary packages in [community].")."</p>";
print "</td>";
print "</tr>";

# MAIN: Bottom Left
print "<tr>";
print "<td class='boxSoft' valign='top'>";

#Hey, how about listing the newest pacakges? :D
$q = "SELECT * FROM Packages ";
$q.= "WHERE DummyPkg != 1 ";
$q.= "ORDER BY GREATEST(SubmittedTS,ModifiedTS) DESC ";
$q.= "LIMIT 0 , 10";
$result = db_query($q,$dbh);
# Table 2
print '<table class="boxSoft">';
print '<tr>';
print '<th colspan="2" class="boxSoftTitle" style="text-align: right">';
print ' <a href="/rss2.php"><img src="/images/rss.gif"></a> <span class="f3">'.__("Recent Updates").' <span class="f5"></span></span>';
print '</th>';
print '</tr>';

while ($row = mysql_fetch_assoc($result)) {
	print '<tr>';
        print '<td class="boxSoft">';

        print '<span class="f4"><span class="blue"><a href="/packages.php?ID='.intval($row["ID"]).'">';
	print $row["Name"]." ".$row["Version"]."</a></span></span>";

        print '</td>';
	print '<td class="boxSoft" style="text-align: right">';

        # figure out the mod string
        $mod_int = intval($row["ModifiedTS"]);
        $sub_int = intval($row["SubmittedTS"]);
        if ($mod_int != 0) {
	  $modstring = gmdate("r", $mod_int);
        }
        elseif ($sub_int != 0) {
          $modstring = '<img src="/images/new.gif"/> '.gmdate("r", $sub_int);
        }
        else {
          $mod_string = "(unknown)";
        }
        print '<span class="f4">'.$modstring.'</span>';
        print '</td>';
	print '</tr>'."\n";
}
print "</td>";
print "</tr>";
print "</table>";
# End Table 2

# MAIN: Bottom Right
print "</td>";
print "<td class='boxSoft' valign='top'>";

# AUR STATISTICS 

$q = "SELECT count(*) FROM Packages,PackageLocations WHERE Packages.LocationID = PackageLocations.ID AND PackageLocations.Location = 'unsupported'";
$result = db_query($q, $dbh);
$row = mysql_fetch_row($result);
$unsupported_count = $row[0];

$q = "SELECT count(*) FROM Packages,PackageLocations WHERE Packages.LocationID = PackageLocations.ID AND PackageLocations.Location = 'community'";
$result = db_query($q, $dbh);
$row = mysql_fetch_row($result);
$community_count = $row[0];

$q = "SELECT count(*) from Users";
$result = db_query($q, $dbh);
$row = mysql_fetch_row($result);
$user_count = $row[0];

$q = "SELECT count(*) from Users,AccountTypes WHERE Users.AccountTypeID = AccountTypes.ID AND AccountTypes.AccountType = 'Trusted User'";
$result = db_query($q, $dbh);
$row = mysql_fetch_row($result);
$tu_count = $row[0];

$targstamp = intval(strtotime("-7 days"));
$q = "SELECT count(*) from Packages WHERE (Packages.SubmittedTS >= $targstamp OR Packages.ModifiedTS >= $targstamp)";
$result = db_query($q, $dbh);
$row = mysql_fetch_row($result);
$update_count = $row[0];

# Added the user statistcs.
# Added by: dsa <dsandrade@gmail.com>
$user = username_from_sid($_COOKIE["AURSID"]);

if (!empty($user)) {
    $q = "SELECT count(*) FROM Packages,PackageLocations,Users WHERE Packages.MaintainerUID = Users.ID AND Packages.LocationID = PackageLocations.ID AND PackageLocations.Location = 'unsupported' AND Users.Username='".mysql_real_escape_string($user)."'";
    $result = db_query($q, $dbh);
    $row = mysql_fetch_row($result);
    $maintainer_unsupported_count = $row[0];
    
    $q = "SELECT count(*) FROM Packages,Users WHERE Packages.OutOfDate = 1 AND Packages.MaintainerUID = Users.ID AND Users.Username='".mysql_real_escape_string($user)."'";
    $result = db_query($q, $dbh);
    $row = mysql_fetch_row($result);
    $flagged_outdated = $row[0];
    
    print "<table class='boxSoft'>";
    
    print "<tr>";
    print "<th colspan='2' class='boxSoftTitle' style='text-align: right'>";
    print "<span class='f3'>".__("My Statistics")."</span>";
    print "</th>";
    print "</tr>";
    
    # Number of packages in unsupported
    print "<tr>";
    print "<td class='boxSoft'>";
    print "<span class='f4'>".__("Packages in unsupported")."</span>";
    print "</td>";
    print "<td class='boxSoft'><span class='f4'>$maintainer_unsupported_count</span></td>";
    print "</tr>";
    
    # If the user is a TU calculate the number of the packages
    $atype = account_from_sid($_COOKIE["AURSID"]);
    
    if ($atype == 'Trusted User') {    
        $q = "SELECT count(*) FROM Packages,PackageLocations,Users WHERE Packages.MaintainerUID = Users.ID AND Packages.LocationID = PackageLocations.ID AND PackageLocations.Location = 'community' AND Users.Username='".mysql_real_escape_string($user)."'";
        $result = db_query($q, $dbh);
        $row = mysql_fetch_row($result);
        $maintainer_community_count = $row[0];
        
        print "<tr>";
        print "<td class='boxSoft'>";
        print "<span class='f4'>".__("Packages in [community]")."</span>";
        print "</td>";
        print "<td class='boxSoft'><span class='f4'>$maintainer_community_count</span></td>";
        print "</tr>";
    }
    
    # Number of outdated packages    
    print "<tr>";
    print "<td class='boxSoft'>";
    print "<span class='f4'>".__("Out-of-date")."</span>";
    print "</td>";
    print "<td class='boxSoft'><span class='f4'>$flagged_outdated</span></td>";
    print "</tr>";    
        
    print "</table><br />";
}

print "<table class='boxSoft'>";

print "<tr>";
print "<th colspan='2' class='boxSoftTitle' style='text-align: right'>";
print "<span class='f3'>".__("Statistics")."</span>";
print "</th>";
print "</tr>";

print "<tr>";
print "<td class='boxSoft'>";
print "<span class='f4'>".__("Packages in unsupported")."</span>";
print "</td>";
print "<td class='boxSoft'><span class='f4'>$unsupported_count</span></td>";
print "</tr>";

print "<tr>";
print "<td class='boxSoft'>";
print "<span class='f4'>".__("Packages in [community]")."</span>";
print "</td>";
print "<td class='boxSoft'><span class='f4'>$community_count</span></td>";
print "</tr>";

print "<tr>";
print "<td class='boxSoft'>";
print "<span class='f4'>".__("Packages added or updated in the past 7 days")."</span>";
print "</td>";
print "<td class='boxSoft'><span class='f4'>$update_count</span></td>";
print "</tr>";

print "<tr>";
print "<td class='boxSoft'>";
print "<span class='blue'><span class='f4'>".__("Registered Users")."</span></span>";
print "</td>";
print "<td class='boxSoft'><span class='f4'>$user_count</span></td>";
print "</tr>";

print "<tr>";
print "<td class='boxSoft'>";
print "<span class='f4'>".__("Trusted Users")."</span>";
print "</td>";
print "<td class='boxSoft'><span class='f4'>$tu_count</span></td>";
print "</tr>";

print "</table>";

# Close out the right column
print "  </td>";
print "</tr>\n";
print "</table>\n";
# End Table 1
echo "<br /><span class='important'>".__("DISCLAIMER")."</span>";
echo "  </div>";
echo "</div>";
html_footer(AUR_VERSION);
# vim: ts=2 sw=2 noet ft=php
?>
