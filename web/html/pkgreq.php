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
html_footer(AUR_VERSION);

