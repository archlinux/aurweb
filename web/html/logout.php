<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");         # access AUR common functions
include_once("acctfuncs.inc.php");         # access AUR common functions

$redirect_uri = '/';

# if they've got a cookie, log them out - need to do this before
# sending any HTML output.
#
if (isset($_COOKIE["AURSID"])) {
	$uid = uid_from_sid($_COOKIE['AURSID']);
	delete_session_id($_COOKIE["AURSID"]);
	# setting expiration to 1 means '1 second after midnight January 1, 1970'
	setcookie("AURSID", "", 1, "/", null, !empty($_SERVER['HTTPS']), true);
	unset($_COOKIE['AURSID']);
	clear_expired_sessions();

	# If the account is linked to an SSO account, disconnect the user from the SSO too.
	if (isset($uid)) {
		$dbh = DB::connect();
		$sso_account_id = $dbh->query("SELECT SSOAccountID FROM Users WHERE ID = " . $dbh->quote($uid))
		                      ->fetchColumn();
		if ($sso_account_id)
			$redirect_uri = '/sso/logout';
	}
}

header("Location: $redirect_uri");

