<p>
	<?= __('You can use this form to permanently delete the AUR account %s.', '<strong>' . htmlspecialchars($username) . '</strong>') ?>
</p>
<p>
	<?= __('%sWARNING%s: This action cannot be undone.', '<strong>', '</strong>') ?>
</p>

<form id="edit-profile-form" action="<?= get_user_uri($username) . 'delete/'; ?>" method="post">
	<fieldset>
		<input type="hidden" name="Action" value="<?= $action ?>" />
		<input type="hidden" name="ID" value="<?= $UID ?>" />
		<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
	</fieldset>
	<fieldset>
		<p>
			<label for="id_passwd"><?= __("Password") ?>:</label>
			<input type="password" size="30" name="passwd" id="id_passwd" value="" />
		</p>

		<p>
			<label class="confirmation"><input type="checkbox" name="confirm" value="1" />
			<?= __("Confirm deletion") ?></label>
		</p>

		<p>
			<input type="submit" class="button" value="<?= __("Delete") ?>" />
		</p>
	</fieldset>
</form>
