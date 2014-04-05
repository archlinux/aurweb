<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");      # access AUR common functions
set_lang();                       # this sets up the visitor's language
include_once('pkgfuncs.inc.php'); # package specific functions
check_sid();                      # see if they're still logged in

# Retrieve package ID and name, unless initialized by the routing framework
if (!isset($pkgid) || !isset($pkgname)) {
	if (isset($_GET['ID'])) {
		$pkgid = intval($_GET['ID']);
		$pkgname = pkg_name_from_id($_GET['ID']);
	} else if (isset($_GET['N'])) {
		$pkgid = pkg_from_name($_GET['N']);
		$pkgname = $_GET['N'];
	} else {
		unset($pkgid, $pkgname);
	}

	if (isset($pkgid) && ($pkgid == 0 || $pkgid == NULL || $pkgname == NULL)) {
		header("HTTP/1.0 404 Not Found");
		include "./404.php";
		return;
	}
}

# Set the title to the current query or package name
if (isset($pkgname)) {
	$title = $pkgname;
} else if (!empty($_GET['K'])) {
	$title = __("Search Criteria") . ": " . $_GET['K'];
} else {
	$title = __("Packages");
}

# Retrieve account type
if (isset($_COOKIE["AURSID"])) {
	$atype = account_from_sid($_COOKIE["AURSID"]);
} else {
	$atype = "";
}

$details = array();
if (isset($pkgname)) {
	$details = pkg_get_details($pkgid);
}

html_header($title, $details);
?>

<?php
if (isset($pkgid)) {
	include('pkg_search_form.php');
	if ($pkgid) {
		if (isset($_COOKIE["AURSID"])) {
			pkg_display_details($pkgid, $details, $_COOKIE["AURSID"]);
		}
		else {
			pkg_display_details($pkgid, $details, null);
		}
	} else {
		print __("Error trying to retrieve package details.")."<br />\n";
	}
} else {
	if (!isset($_GET['K']) && !isset($_GET['SB'])) {
		$_GET['SB'] = 'v';
		$_GET['SO'] = 'd';
	}
	if (isset($_COOKIE["AURSID"])) {
		pkg_search_page($_COOKIE["AURSID"]);
	} else {
		pkg_search_page();
	}
}

html_footer(AUR_VERSION);

