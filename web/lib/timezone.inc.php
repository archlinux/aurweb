<?php
set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

/**
 * Generate an associative of the PHP timezones and display text.
 *
 * @return array PHP Timezone => Displayed Description
 */
function generate_timezone_list() {
	$php_timezones = DateTimeZone::listIdentifiers(DateTimeZone::ALL);

	$offsets = array();
	foreach ($php_timezones as $timezone) {
		$tz = new DateTimeZone($timezone);
		$offset = $tz->getOffset(new DateTime());
		$offsets[$timezone] = "(UTC" . ($offset < 0 ? "-" : "+") . gmdate("H:i", abs($offset)) .
			") " . $timezone;
	}

	asort($offsets);
	return $offsets;
}

/**
 * Set the timezone for the user.
 *
 * @return null
 */
function set_tz() {
	$timezones = generate_timezone_list();
	$update_cookie = false;

	if (isset($_COOKIE["AURTZ"])) {
		$timezone = $_COOKIE["AURTZ"];
	} elseif (isset($_COOKIE["AURSID"])) {
		$dbh = DB::connect();
		$q = "SELECT Timezone FROM Users, Sessions ";
		$q .= "WHERE Users.ID = Sessions.UsersID ";
		$q .= "AND Sessions.SessionID = ";
		$q .= $dbh->quote($_COOKIE["AURSID"]);
		$result = $dbh->query($q);

		if ($result) {
			$timezone = $result->fetchColumn(0);
		}

		$update_cookie = true;
	}

	if (!isset($timezone) || !array_key_exists($timezone, $timezones)) {
		$timezone = config_get("options", "default_timezone");
	}
	date_default_timezone_set($timezone);

	if ($update_cookie) {
		$timeout = intval(config_get("options", "persistent_cookie_timeout"));
		$cookie_time = time() + $timeout;
		setcookie("AURTZ", $timezone, $cookie_time, "/");
	}
}
