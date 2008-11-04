<?php

include_once('aur.inc');

function updates_table($dbh)
{
	$q = 'SELECT * FROM Packages WHERE DummyPkg != 1 ORDER BY GREATEST(SubmittedTS,ModifiedTS) DESC LIMIT 0 , 10';
	$newest_packages = db_query($q, $dbh);
	include('stats/updates_table.php');
}

function user_table($user, $dbh)
{

	$base_q = 'SELECT count(*) FROM Packages,PackageLocations,Users WHERE Packages.MaintainerUID = Users.ID AND Packages.LocationID = PackageLocations.ID AND PackageLocations.Location = "%s" AND Users.Username="' .
	mysql_real_escape_string($user).'"';

	$result = db_query(sprintf($base_q, 'unsupported'), $dbh);
	$row = mysql_fetch_row($result);
	$maintainer_unsupported_count = $row[0];

	$q = "SELECT count(*) FROM Packages,Users WHERE Packages.OutOfDate = 1 AND Packages.MaintainerUID = Users.ID AND Users.Username='" .
	mysql_real_escape_string($user)."'";

	$result = db_query($q, $dbh);
	$row = mysql_fetch_row($result);
	$flagged_outdated = $row[0];

	# If the user is a TU calculate the number of the packages
	$atype = account_from_sid($_COOKIE["AURSID"]);

	if (($atype == 'Trusted User') || ($atype == 'Developer')) {
		$result = db_query(sprintf($base_q, 'community'), $dbh);
		$row = mysql_fetch_row($result);
		$maintainer_community_count = $row[0];
	}

	include('stats/user_table.php');
}

function general_stats_table($dbh)
{
	# AUR statistics
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

	include('stats/general_stats_table.php');
}

