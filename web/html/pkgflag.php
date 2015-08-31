<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
include_once("pkgfuncs.inc.php");

set_lang();
check_sid();

html_header(__("Flag Package Out-Of-Date"));

if (has_credential(CRED_PKGBASE_FLAG)): ?>
<div class="box">
	<h2><?= __('Flag Package Out-Of-Date: %s', htmlspecialchars($pkgbase_name)) ?></h2>
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
	</p>
	<form action="<?= get_uri('/pkgbase/'); ?>" method="post">
		<fieldset>
			<input type="hidden" name="IDs[<?= $base_id ?>]" value="1" />
			<input type="hidden" name="ID" value="<?= $base_id ?>" />
			<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
			<p><input type="submit" class="button" name="do_Flag" value="<?= __("Flag") ?>" /></p>
		</fieldset>
	</form>
</div>

<?php
else:
	print __("Only registered users can flag packages out-of-date.");
endif;

html_footer(AURWEB_VERSION);
