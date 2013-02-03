<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");         # access AUR common functions
include_once("acctfuncs.inc.php");         # access AUR common functions


# if they've got a cookie, log them out - need to do this before
# sending any HTML output.
#
if (isset($_COOKIE["AURSID"])) {
	delete_session_id($_COOKIE["AURSID"]);
	# setting expiration to 1 means '1 second after midnight January 1, 1970'
	setcookie("AURSID", "", 1, "/", null, !empty($_SERVER['HTTPS']), true);
	unset($_COOKIE['AURSID']);
	clear_expired_sessions();
}

header('Location: /');

