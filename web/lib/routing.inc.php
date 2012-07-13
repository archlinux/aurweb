<?php

$ROUTES = array(
	'' => 'home.php',
	'/index.php' => 'home.php',
	'/packages' => 'packages.php',
	'/register' => 'account.php',
	'/accounts' => 'account.php',
	'/login' => 'login.php',
	'/logout' => 'logout.php',
	'/passreset' => 'passreset.php',
	'/rpc' => 'rpc.php',
	'/rss' => 'rss.php',
	'/submit' => 'pkgsubmit.php',
	'/tu' => 'tu.php',
	'/voters' => 'voters.php',
	'/addvote' => 'addvote.php',
);

function get_route($path) {
	global $ROUTES;

	if (isset($ROUTES[$path])) {
		return $ROUTES[$path];
	} else {
		return NULL;
	}
}

function get_uri($path) {
	global $USE_VIRTUAL_URLS;
	global $ROUTES;

	if ($USE_VIRTUAL_URLS) {
		return $path;
	} else {
		return get_route($path);
	}
}
