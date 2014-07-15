<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
include_once("pkgfuncs.inc.php");

set_lang();
check_sid();

if (isset($base_id)) {
	html_header(__("File Request"));
	include('pkgreq_form.php');
} elseif (isset($pkgreq_id)) {
	html_header(__("Close Request"));
	$pkgbase_name = pkgreq_get_pkgbase_name($pkgreq_id);
	include('pkgreq_close_form.php');
} else {
	if (!has_credential(CRED_PKGREQ_LIST)) {
		header('Location: /');
		exit();
	}

	/* Sanitize paging variables. */
	if (isset($_GET['O'])) {
		$_GET['O'] = max(intval($_GET['O']), 0);
	} else {
		$_GET['O'] = 0;
	}

	if (isset($_GET["PP"])) {
		$_GET["PP"] = bound(intval($_GET["PP"]), 50, 250);
	} else {
		$_GET["PP"] = 50;
	}

	$results = pkgreq_list($_GET['O'], $_GET['PP']);
	$total = pkgreq_count();

	/* Calculate the results to use. */
	$first = $_GET['O'] + 1;

	/* Calculation of pagination links. */
	$per_page = ($_GET['PP'] > 0) ? $_GET['PP'] : 50;
	$current = ceil($first / $per_page);
	$pages = ceil($total / $per_page);
	$templ_pages = array();

	if ($current > 1) {
		$templ_pages['&laquo; ' . __('First')] = 0;
		$templ_pages['&lsaquo; ' . __('Previous')] = ($current - 2) * $per_page;
	}

	if ($current - 5 > 1)
		$templ_pages["..."] = false;

	for ($i = max($current - 5, 1); $i <= min($pages, $current + 5); $i++) {
		$templ_pages[$i] = ($i - 1) * $per_page;
	}

	if ($current + 5 < $pages)
		$templ_pages["... "] = false;

	if ($current < $pages) {
		$templ_pages[__('Next') . ' &rsaquo;'] = $current * $per_page;
		$templ_pages[__('Last') . ' &raquo;'] = ($pages - 1) * $per_page;
	}

	$SID = $_COOKIE['AURSID'];

	html_header(__("Requests"));
	include('pkgreq_results.php');
}

html_footer(AUR_VERSION);

