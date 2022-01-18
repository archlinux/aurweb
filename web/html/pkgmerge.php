<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
include_once("pkgfuncs.inc.php");

html_header(__("Package Merging"));

if (has_credential(CRED_PKGBASE_DELETE)): ?>
<div class="box">
	<h2><?= __('Merge Package') ?>: <?= htmlspecialchars($pkgbase_name) ?></h2>
	<p>
		<?= __('Use this form to merge the package base %s%s%s into another package. ',
			'<strong>', htmlspecialchars($pkgbase_name), '</strong>'); ?>
		<?= __('The following packages will be deleted: '); ?>
	</p>
	<ul>
		<?php foreach(pkgbase_get_pkgnames($base_id) as $pkgname): ?>
		<li><?= htmlspecialchars($pkgname) ?></li>
		<?php endforeach; ?>
	</ul>
	<p>
		<?= __('Once the package has been merged it cannot be reversed. '); ?>
		<?= __('Enter the package name you wish to merge the package into. '); ?>
		<?= __('Select the checkbox to confirm action.') ?>
	</p>
	<form id="merge-form" action="<?= get_pkgbase_uri($pkgbase_name); ?>" method="post">
		<fieldset>
			<input type="hidden" name="IDs[<?= $base_id ?>]" value="1" />
			<input type="hidden" name="ID" value="<?= $base_id ?>" />
			<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
			<?php if (isset($_GET['via'])): ?>
			<input type="hidden" name="via" value="<?= intval($_GET['via']) ?>" />
			<?php endif; ?>
			<script type="text/javascript" src="/js/typeahead.js"></script>
			<script type="text/javascript">
			document.addEventListener('DOMContentLoaded', function() {
				const input = document.getElementById('merge_Into');
				const form = document.getElementById('merge-form');
				const type = "suggest-pkgbase";
				typeahead.init(type, input, form, false);
			});
			</script>
			<p><label id="merge-into" for="merge_Into" ><?= __("Merge into:") ?></label>
			<input type="text" id="merge_Into" name="merge_Into" value="<?= isset($_GET['into']) ? $_GET['into'] : '' ?>" autocomplete="off"/></p>
			<p><label class="confirmation"><input type="checkbox" name="confirm" value="1" />
			<?= __("Confirm package merge") ?></label></p>
			<p><input type="submit" class="button" name="do_Delete" value="<?= __("Merge") ?>" /></p>
		</fieldset>
	</form>
</div>

<?php else:
	print __("Only Trusted Users and Developers can merge packages.");
endif;

html_footer(AURWEB_VERSION);
