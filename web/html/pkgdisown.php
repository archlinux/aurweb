<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
include_once("pkgfuncs.inc.php");

html_header(__("Disown Package"));

$action = "do_Disown";

$maintainer_uids = array(pkgbase_maintainer_uid($base_id));
$comaintainers = pkgbase_get_comaintainers($base_id);
$comaintainer_uids = pkgbase_get_comaintainer_uids(array($base_id));

if (has_credential(CRED_PKGBASE_DISOWN, array_merge($maintainer_uids, $comaintainer_uids))): ?>
<div class="box">
	<h2><?= __('Disown Package') ?>: <?= htmlspecialchars($pkgbase_name) ?></h2>
	<p>
		<?= __('Use this form to disown the package base %s%s%s which includes the following packages: ',
			'<strong>', htmlspecialchars($pkgbase_name), '</strong>'); ?>
	</p>
	<ul>
		<?php foreach(pkgbase_get_pkgnames($base_id) as $pkgname): ?>
		<li><?= htmlspecialchars($pkgname) ?></li>
		<?php endforeach; ?>
	</ul>
	<p>

		<?php if (in_array(uid_from_sid($_COOKIE["AURSID"]), $comaintainer_uids) && !has_credential(CRED_PKGBASE_DISOWN)):
			$action = "do_DisownComaintainer"; ?>
			<?= __("By selecting the checkbox, you confirm that you want to no longer be a package co-maintainer.") ?>
		<?php elseif (count($comaintainers) > 0 && !has_credential(CRED_PKGBASE_DISOWN)): ?>
		<?= __('By selecting the checkbox, you confirm that you want to disown the package and transfer ownership to %s%s%s.',
			'<strong>', $comaintainers[0], '</strong>'); ?>
		<?php else: ?>
		<?= __('By selecting the checkbox, you confirm that you want to disown the package.') ?>
		<?php endif; ?>
	</p>
	<form action="<?= get_pkgbase_uri($pkgbase_name); ?>" method="post">
		<fieldset>
			<input type="hidden" name="IDs[<?= $base_id ?>]" value="1" />
			<input type="hidden" name="ID" value="<?= $base_id ?>" />
			<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
			<?php if (isset($_GET['via'])): ?>
			<input type="hidden" name="via" value="<?= intval($_GET['via']) ?>" />
			<?php endif; ?>
			<p><label class="confirmation"><input type="checkbox" name="confirm" value="1" />
			<?= __("Confirm to disown the package") ?></label</p>
			<p><input type="submit" class="button" name="<?= $action ?>" value="<?= __("Disown") ?>" /></p>
		</fieldset>
	</form>
</div>

<?php else:
	print __("Only Trusted Users and Developers can disown packages.");
endif;

html_footer(AURWEB_VERSION);
