<?php

$ROUTES = array(
	'' => 'home.php',
	'/index.php' => 'home.php',
	'/packages' => 'packages.php',
	'/register' => 'account.php',
	'/account' => 'account.php',
	'/accounts' => 'account.php',
	'/login' => 'login.php',
	'/logout' => 'logout.php',
	'/passreset' => 'passreset.php',
	'/rpc' => 'rpc.php',
	'/rss' => 'rss.php',
	'/submit' => 'pkgsubmit.php',
	'/tu' => 'tu.php',
	'/addvote' => 'addvote.php',
);

$PKG_PATH = '/packages';
$USER_PATH = '/account';

function get_route($path) {
	global $ROUTES;

	$path = rtrim($path, '/');
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

function get_pkg_route() {
	global $PKG_PATH;
	return $PKG_PATH;
}

function get_pkg_uri($pkgname) {
	global $USE_VIRTUAL_URLS;
	global $PKG_PATH;

	if ($USE_VIRTUAL_URLS) {
		return $PKG_PATH . '/' . urlencode($pkgname) . '/';
	} else {
		return '/' . get_route($PKG_PATH) . '?N=' . urlencode($pkgname);
	}
}

function get_user_route() {
	global $USER_PATH;
	return $USER_PATH;
}

function get_user_uri($username) {
	global $USE_VIRTUAL_URLS;
	global $USER_PATH;

	if ($USE_VIRTUAL_URLS) {
		return $USER_PATH . '/' . urlencode($username) . '/';
	} else {
		return '/' . get_route($USER_PATH) . '?U=' . urlencode($username);
	}
}
