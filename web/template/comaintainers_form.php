<div class="box">
	<h2><?= __('Manage Co-maintainers') ?>: <? htmlspecialchars($pkgbase_name) ?></h2>
	<p>
		<?= __('Use this form to add co-maintainers for %s%s%s (one user name per line):',
			'<strong>', htmlspecialchars($pkgbase_name), '</strong>'); ?>
	</p>
	<form action="<?= get_pkgbase_uri($pkgbase_name); ?>" method="post">
		<fieldset>
			<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
			<p>
				<label for="id_users"><?= __("Users") ?>:</label>
				<textarea name="users" id="id_users" rows="5" cols="50"><?= htmlspecialchars(implode("\n", $users)) ?></textarea>
			</p>
			<p>
				<input type="submit" class="button" name="do_EditComaintainers" value="<?= __("Save") ?>" />
			</p>
		</fieldset>
	</form>
</div>

