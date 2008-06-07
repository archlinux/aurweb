<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../lang');

include("pkgfuncs_po.inc"); # Add to handle the i18n of My Packages
include("aur.inc");
set_lang();
check_sid();
html_header(__("Home"));

# Hey, how about listing the newest pacakges? :D
$q = "SELECT * FROM Packages ";
$q.= "WHERE DummyPkg != 1 ";
$q.= "ORDER BY GREATEST(SubmittedTS,ModifiedTS) DESC ";
$q.= "LIMIT 0 , 10";
$result_newest = db_query($q,$dbh);

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
    
    # If the user is a TU calculate the number of the packages
    $atype = account_from_sid($_COOKIE["AURSID"]);
    
    if ($atype == 'Trusted User') {    
        $q = "SELECT count(*) FROM Packages,PackageLocations,Users WHERE Packages.MaintainerUID = Users.ID AND Packages.LocationID = PackageLocations.ID AND PackageLocations.Location = 'community' AND Users.Username='".mysql_real_escape_string($user)."'";
        $result = db_query($q, $dbh);
        $row = mysql_fetch_row($result);
        $maintainer_community_count = $row[0];
    }
}

include('front_page.php');

html_footer(AUR_VERSION);

# vim: ts=2 sw=2 noet ft=php
?>
