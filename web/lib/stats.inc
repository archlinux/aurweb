<?php

include_once('aur.inc');

# APC configuration variables
$apc_prefix = 'aur:';
$apc_ttl = 600;

# Check if APC extension is loaded
if (!defined('EXTENSION_LOADED_APC'))
	define('EXTENSION_LOADED_APC', extension_loaded('apc'));

# run a simple db query, retrieving and/or caching the value if APC
# is available for use
#
function db_cache_value($dbq, $dbh, $key)
{
	global $apc_ttl;
	$bool = false;
	if(EXTENSION_LOADED_APC) {
		$ret = apc_fetch($key, $bool);
	}
	if(!$bool) {
		$result = db_query($dbq, $dbh);
		$row = mysql_fetch_row($result);
		$ret = $row[0];
		if (EXTENSION_LOADED_APC) {
			apc_store($key, $ret, $apc_ttl);
		}
	}
	return $ret;
}

function updates_table($dbh)
{
	global $apc_prefix, $apc_ttl;
	$key = $apc_prefix . 'recent_updates';
	if(!(EXTENSION_LOADED_APC && ($newest_packages = apc_fetch($key)))) {
		$q = 'SELECT * FROM Packages WHERE DummyPkg != 1 ORDER BY GREATEST(SubmittedTS,ModifiedTS) DESC LIMIT 0 , 10';
		$result = db_query($q, $dbh);

		$newest_packages = new ArrayObject();
		while ($row = mysql_fetch_assoc($result)) {
			$newest_packages->append($row);
		}
		if (EXTENSION_LOADED_APC) {
			apc_store($key, $newest_packages, $apc_ttl);
		}
	}
	include('stats/updates_table.php');
}

function user_table($user, $dbh)
{
	global $apc_prefix;
	$escuser = mysql_real_escape_string($user);
	$base_q = "SELECT count(*) FROM Packages,PackageLocations,Users WHERE Packages.MaintainerUID = Users.ID AND Packages.LocationID = PackageLocations.ID AND PackageLocations.Location = '%s' AND Users.Username='" . $escuser . "'";

	$maintainer_unsupported_count = db_cache_value(sprintf($base_q, 'unsupported'), $dbh,
		$apc_prefix . 'user_unsupported_count:' . $escuser);

	$q = "SELECT count(*) FROM Packages,Users WHERE Packages.OutOfDateTS IS NOT NULL AND Packages.MaintainerUID = Users.ID AND Users.Username='" . $escuser . "'";

	$flagged_outdated = db_cache_value($q, $dbh,
		$apc_prefix . 'user_flagged_outdated:' . $escuser);

	# If the user is a TU calculate the number of the packages
	$atype = account_from_sid($_COOKIE["AURSID"]);

	include('stats/user_table.php');
}

function general_stats_table($dbh)
{
	global $apc_prefix;
	# AUR statistics
	$q = "SELECT count(*) FROM Packages,PackageLocations WHERE Packages.LocationID = PackageLocations.ID AND PackageLocations.Location = 'unsupported'";
	$unsupported_count = db_cache_value($q, $dbh, $apc_prefix . 'unsupported_count');

	$q = "SELECT count(*) from Users";
	$user_count = db_cache_value($q, $dbh, $apc_prefix . 'user_count');

	$q = "SELECT count(*) from Users,AccountTypes WHERE Users.AccountTypeID = AccountTypes.ID AND AccountTypes.AccountType = 'Trusted User'";
	$tu_count = db_cache_value($q, $dbh, $apc_prefix . 'tu_count');

	$targstamp = intval(strtotime("-7 days"));
	$q = "SELECT count(*) from Packages WHERE (Packages.SubmittedTS >= $targstamp OR Packages.ModifiedTS >= $targstamp)";
	$update_count = db_cache_value($q, $dbh, $apc_prefix . 'update_count');

	include('stats/general_stats_table.php');
}

