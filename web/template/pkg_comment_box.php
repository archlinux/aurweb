<div id="generic-form" class="box">
	<h2><?= (isset($comment_id)) ? __('Edit comment for: %s', htmlspecialchars($pkgbase_name)) : __("Add Comment"); ?></h2>
	<?php include 'pkg_comment_form.php' ?>
</div>
