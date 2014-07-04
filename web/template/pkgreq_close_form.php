<div class="box">
	<h2><?= __('Close Request: %s', htmlspecialchars($pkgbase_name)) ?></h2>
	<p>
		<?= __('Use this form to close the request for package base %s%s%s.',
			'<strong>', htmlspecialchars($pkgbase_name), '</strong>'); ?>
	</p>
	<form action="<?= get_uri('/pkgbase/'); ?>" method="post">
		<fieldset>
			<input type="hidden" name="reqid" value="<?= $pkgreq_id ?>" />
			<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
			<p>
				<label for="id_reason"><?= __("Reason") ?>:</label>
				<select name="reason" id="id_reason">
					<option value="accepted"><?= __('Accepted') ?></option>
					<option value="rejected"><?= __('Rejected') ?></option>
				</select>
			</p>
			<p>
				<input type="submit" class="button" name="do_CloseRequest" value="<?= __("Close Request") ?>" />
			</p>
		</fieldset>
	</form>
</div>

