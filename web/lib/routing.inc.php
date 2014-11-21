<?php

include_once("confparser.inc.php");

$ROUTES = array(
	'' => 'home.php',
	'/index.php' => 'home.php',
	'/packages' => 'packages.php',
	'/pkgbase' => 'pkgbase.php',
	'/requests' => 'pkgreq.php',
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
$PKGBASE_PATH = '/pkgbase';
$PKGREQ_PATH = '/requests';
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
	return $path;
}

function get_pkg_route() {
	global $PKG_PATH;
	return $PKG_PATH;
}

function get_pkgbase_route() {
	global $PKGBASE_PATH;
	return $PKGBASE_PATH;
}

function get_pkgreq_route() {
	global $PKGREQ_PATH;
	return $PKGREQ_PATH;
}

function get_pkg_uri($pkgname) {
	global $PKG_PATH;
	return $PKG_PATH . '/' . urlencode($pkgname) . '/';
}

function get_pkgbase_uri($pkgbase_name) {
	global $PKGBASE_PATH;
	return $PKGBASE_PATH . '/' . urlencode($pkgbase_name) . '/';
}

function get_user_route() {
	global $USER_PATH;
	return $USER_PATH;
}

function get_user_uri($username) {
	global $USER_PATH;
	return $USER_PATH . '/' . urlencode($username) . '/';
}
