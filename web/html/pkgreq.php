<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
include_once("pkgfuncs.inc.php");

set_lang();
check_sid();

if (!isset($base_id)) {
	if (!check_user_privileges()) {
		header('Location: /');
		exit();
	}

	$results = pkgreq_list();
	$total = count($results);

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
} else {
	html_header(__("File Request"));
	include('pkgreq_form.php');
}

html_footer(AUR_VERSION);

