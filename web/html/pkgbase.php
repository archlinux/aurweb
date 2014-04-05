<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
set_lang();
include_once('pkgfuncs.inc.php');
check_sid();

/*
 * Retrieve package base ID and name, unless initialized by the routing
 * framework.
 */
if (!isset($base_id) || !isset($pkgbase_name)) {
	if (isset($_GET['ID'])) {
		$base_id = intval($_GET['ID']);
		$pkgbase_name = pkgbase_name_from_id($_GET['ID']);
	} else if (isset($_GET['N'])) {
		$base_id = pkgbase_from_name($_GET['N']);
		$pkgbase_name = $_GET['N'];
	} else {
		unset($base_id, $pkgbase_name);
	}

	if ($base_id == 0 || $base_id == NULL || $pkgbase_name == NULL) {
		header("HTTP/1.0 404 Not Found");
		include "./404.php";
		return;
	}
}

/* Set the title to package base name. */
$title = $pkgbase_name;

/* Retrieve account type. */
if (isset($_COOKIE["AURSID"])) {
	$atype = account_from_sid($_COOKIE["AURSID"]);
} else {
	$atype = "";
}

$details = get_pkgbase_details($base_id);
html_header($title, $details);
?>

<?php
include('pkg_search_form.php');
if (isset($_COOKIE["AURSID"])) {
	display_pkgbase_details($base_id, $details, $_COOKIE["AURSID"]);
} else {
	display_pkgbase_details($base_id, $details, null);
}

html_footer(AUR_VERSION);

