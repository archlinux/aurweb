<?php

include_once('aur.inc.php');

/**
 * Display the most recent 10 packages
 *
 * @return void
 */
function updates_table() {
	$dbh = DB::connect();
	$key = 'recent_updates';
	if(!($newest_packages = get_cache_value($key))) {
		$q = 'SELECT Packages.Name, Version, ModifiedTS, SubmittedTS ';
		$q.= 'FROM Packages INNER JOIN PackageBases ON ';
		$q.= 'Packages.PackageBaseID = PackageBases.ID ';
		$q.= 'WHERE PackageBases.PackagerUID IS NOT NULL ';
		$q.= 'ORDER BY ModifiedTS DESC LIMIT 15';
		$result = $dbh->query($q);

		$newest_packages = new ArrayObject();
		while ($row = $result->fetch(PDO::FETCH_ASSOC)) {
			$newest_packages->append($row);
		}
		set_cache_value($key, $newest_packages);
	}
	include('stats/updates_table.php');
}

/**
 * Display a user's statistics table
 *
 * @param string $userid The user ID of the person to get package statistics for
 *
 * @return void
 */
function user_table($userid) {
	$base_q = "SELECT COUNT(*) FROM PackageBases ";
	$base_q.= "WHERE MaintainerUID = " . $userid . " ";
	$base_q.= "AND PackagerUID IS NOT NULL";

	$user_pkg_count = db_cache_value($base_q, 'user_pkg_count:' . $userid);

	$q = "SELECT COUNT(*) FROM PackageBases ";
	$q.= "WHERE OutOfDateTS IS NOT NULL ";
	$q.= "AND MaintainerUID = " . $userid . " ";
	$q.= "AND PackagerUID IS NOT NULL";

	$flagged_outdated = db_cache_value($q, 'user_flagged_outdated:' . $userid);

	include('stats/user_table.php');
}

/**
 * Display the general package statistics table
 *
 * @return void
 */
function general_stats_table() {
	# AUR statistics
	$q = "SELECT COUNT(*) FROM PackageBases WHERE PackagerUID IS NOT NULL";
	$pkg_count = db_cache_value($q, 'pkg_count');

	$q = "SELECT COUNT(*) FROM PackageBases ";
	$q.= "WHERE MaintainerUID IS NULL ";
	$q.= "AND PackagerUID IS NOT NULL";
	$orphan_count = db_cache_value($q, 'orphan_count');

	$q = "SELECT count(*) FROM Users";
	$user_count = db_cache_value($q, 'user_count');

	$q = "SELECT count(*) FROM Users,AccountTypes WHERE Users.AccountTypeID = AccountTypes.ID AND (AccountTypes.AccountType = 'Trusted User' OR AccountTypes.AccountType = 'Trusted User & Developer')";
	$tu_count = db_cache_value($q, 'tu_count');

	$targstamp = intval(strtotime("-7 days"));
	$yearstamp = intval(strtotime("-1 year"));

	$q = "SELECT COUNT(*) FROM PackageBases ";
	$q.= "WHERE SubmittedTS >= $targstamp ";
	$q.= "AND PackagerUID IS NOT NULL";
	$add_count = db_cache_value($q, 'add_count');

	/*
	 * A package whose last modification time differs less than an hour
	 * from the initial submission time is considered new.
	 */

	$q = "SELECT COUNT(*) FROM PackageBases ";
	$q.= "WHERE ModifiedTS >= $targstamp ";
	$q.= "AND ModifiedTS - SubmittedTS >= 3600 ";
	$q.= "AND PackagerUID IS NOT NULL";
	$update_count = db_cache_value($q, 'update_count');

	$q = "SELECT COUNT(*) FROM PackageBases ";
	$q.= "WHERE ModifiedTS >= $yearstamp ";
	$q.= "AND ModifiedTS - SubmittedTS >= 3600 ";
	$q.= "AND PackagerUID IS NOT NULL";
	$update_year_count = db_cache_value($q, 'update_year_count');

	$q = "SELECT COUNT(*) FROM PackageBases ";
	$q.= "WHERE ModifiedTS - SubmittedTS < 3600 ";
	$q.= "AND PackagerUID IS NOT NULL";
	$never_update_count = db_cache_value($q, 'never_update_count');

	include('stats/general_stats_table.php');
}
