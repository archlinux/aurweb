<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
include_once("pkgfuncs.inc.php");

set_lang();
check_sid();

html_header(__("File Request"));

if (!check_user_privileges()) {
	header('Location: /');
	exit();
}

if (!isset($base_id)) {
	$results = pkgbase_request_list();
	$total = count($results);

	/* Sanitize paging variables. */
	if (isset($_GET['O'])) {
		$_GET['O'] = intval($_GET['O']);
		if ($_GET['O'] < 0)
			$_GET['O'] = 0;
	} else {
		$_GET['O'] = 0;
	}

	if (isset($_GET["PP"])) {
		$_GET["PP"] = intval($_GET["PP"]);
		if ($_GET["PP"] < 50)
			$_GET["PP"] = 50;
		else if ($_GET["PP"] > 250)
			$_GET["PP"] = 250;
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
	include('pkgreq_results.php');
} else {
?>

<div class="box">
	<h2><?= __('File Request: %s', htmlspecialchars($pkgbase_name)) ?></h2>
	<p>
		<?= __('Use this form to file a request against package base %s%s%s which includes the following packages:',
			'<strong>', htmlspecialchars($pkgbase_name), '</strong>'); ?>
	</p>
	<ul>
		<?php foreach(pkgbase_get_pkgnames($base_id) as $pkgname): ?>
		<li><?= htmlspecialchars($pkgname) ?></li>
		<?php endforeach; ?>
	</ul>
	<form action="<?= get_uri('/pkgbase/'); ?>" method="post">
		<fieldset>
			<input type="hidden" name="IDs[<?= $base_id ?>]" value="1" />
			<input type="hidden" name="ID" value="<?= $base_id ?>" />
			<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
			<p>
				<label for="id_type"><?= __("Request type") ?>:</label>
				<select name="type" id="id_type">
					<option value="deletion"><?= __('Deletion') ?></option>
					<option value="orphan"><?= __('Orphan') ?></option>
				</select>
			</p>
			<p>
				<label for="id_comments"><?= __("Comments") ?>:</label>
				<textarea name="comments" id="id_comments" rows="5" cols="50"></textarea>
			</p>
			<p>
				<input type="submit" class="button" name="do_FileRequest" value="<?= __("File Request") ?>" />
			</p>
		</fieldset>
	</form>
</div>

<?php
}

html_footer(AUR_VERSION);

