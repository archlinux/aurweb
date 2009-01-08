<?php

include_once('aur.inc');

$apc_prefix = 'aur:';
# Check if APC extension is loaded
if (!defined('EXTENSION_LOADED_APC'))
	define('EXTENSION_LOADED_APC', extension_loaded('apc'));

# run a simple db query, retrieving and/or caching the value if APC
# is available for use
#
function db_cache_value($dbq, $dbh, $key)
{
	if(!(EXTENSION_LOADED_APC && ($ret = apc_fetch($key)))) {
		$result = db_query($dbq, $dbh);
		$row = mysql_fetch_row($result);
		$ret = $row[0];
		# set the TTL here in seconds: 300 seconds = 5 minutes

		if (EXTENSION_LOADED_APC) {
			apc_store($key, $ret, 300);
		}
	}
	return $ret;
}

function updates_table($dbh)
{
	global $apc_prefix;
	$key = $apc_prefix . 'recent_updates';
	if(!(EXTENSION_LOADED_APC && ($newest_packages = apc_fetch($key)))) {
		$q = 'SELECT * FROM Packages WHERE DummyPkg != 1 ORDER BY GREATEST(SubmittedTS,ModifiedTS) DESC LIMIT 0 , 10';
		$result = db_query($q, $dbh);

		$newest_packages = new ArrayObject();
		while ($row = mysql_fetch_assoc($result)) {
			$newest_packages->append($row);
		}

		if (EXTENSION_LOADED_APC) {
			apc_store($key, $newest_packages, 300);
		}
	}
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
	global $apc_prefix;
	# AUR statistics
	$q = "SELECT count(*) FROM Packages,PackageLocations WHERE Packages.LocationID = PackageLocations.ID AND PackageLocations.Location = 'unsupported'";
	$unsupported_count = db_cache_value($q, $dbh, $apc_prefix . 'unsupported_count');

	$q = "SELECT count(*) FROM Packages,PackageLocations WHERE Packages.LocationID = PackageLocations.ID AND PackageLocations.Location = 'community'";
	$community_count = db_cache_value($q, $dbh, $apc_prefix . 'community_count');

	$q = "SELECT count(*) from Users";
	$user_count = db_cache_value($q, $dbh, $apc_prefix . 'user_count');

	$q = "SELECT count(*) from Users,AccountTypes WHERE Users.AccountTypeID = AccountTypes.ID AND AccountTypes.AccountType = 'Trusted User'";
	$tu_count = db_cache_value($q, $dbh, $apc_prefix . 'tu_count');

	$targstamp = intval(strtotime("-7 days"));
	$q = "SELECT count(*) from Packages WHERE (Packages.SubmittedTS >= $targstamp OR Packages.ModifiedTS >= $targstamp)";
	$update_count = db_cache_value($q, $dbh, $apc_prefix . 'update_count');

	include('stats/general_stats_table.php');
}

