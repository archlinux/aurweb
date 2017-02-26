<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
include_once("pkgfuncs.inc.php");

set_lang();
check_sid();

/* Grab the list of package base IDs to be operated on. */
$ids = array();
if (isset($_POST['IDs'])) {
	foreach ($_POST['IDs'] as $id => $i) {
		$id = intval($id);
		if ($id > 0) {
			$ids[] = $id;
		}
	}
}

/* Perform package base actions. */
$ret = false;
$output = "";
if (check_token()) {
	if (current_action("do_Flag")) {
		list($ret, $output) = pkgbase_flag($ids, $_POST['comments']);
	}

	if ($ret) {
		header('Location: ' . get_pkgbase_uri($pkgbase_name) . $fragment);
		exit();
	}
}

/* Get default comment. */
$comment = '';
if (isset($_POST['comments'])) {
	$comment = $_POST['comments'];
}

html_header(__("Flag Package Out-Of-Date"));

if (has_credential(CRED_PKGBASE_FLAG)): ?>
<div class="box">
	<h2><?= __('Flag Package Out-Of-Date') ?>: <?= htmlspecialchars($pkgbase_name) ?></h2>
	<p>
		<?= __('Use this form to flag the package base %s%s%s and the following packages out-of-date: ',
			'<strong>', htmlspecialchars($pkgbase_name), '</strong>'); ?>
	</p>
	<ul>
		<?php foreach(pkgbase_get_pkgnames($base_id) as $pkgname): ?>
		<li><?= htmlspecialchars($pkgname) ?></li>
		<?php endforeach; ?>
	</ul>
	<p>
		<?= __('Please do %snot%s use this form to report bugs. Use the package comments instead.',
			'<strong>', '</strong>'); ?>
		<?= __('Enter details on why the package is out-of-date below, preferably including links to the release announcement or the new release tarball.'); ?>
	</p>

	<?php if ($output && !$ret): ?>
	<ul class="errorlist"><li><?= htmlspecialchars($output) ?></li></ul>
	<?php endif; ?>

	<form action="<?= get_pkgbase_uri($pkgbase_name); ?>flag/" method="post">
		<fieldset>
			<input type="hidden" name="IDs[<?= $base_id ?>]" value="1" />
			<input type="hidden" name="ID" value="<?= $base_id ?>" />
			<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
			<p>
				<label for="id_comments"><?= __("Comments") ?>:</label>
				<textarea name="comments" id="id_comments" rows="5" cols="50"><?= htmlspecialchars($comment) ?></textarea>
			</p>
			<p><input type="submit" class="button" name="do_Flag" value="<?= __("Flag") ?>" /></p>
		</fieldset>
	</form>
</div>

<?php
else:
	print __("Only registered users can flag packages out-of-date.");
endif;

html_footer(AURWEB_VERSION);
