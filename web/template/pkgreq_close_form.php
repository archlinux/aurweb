<div class="box">
	<h2><?= __('Close Request: %s', htmlspecialchars($pkgbase_name)) ?></h2>
	<p>
		<?= __('Use this form to close the request for package base %s%s%s.',
			'<strong>', htmlspecialchars($pkgbase_name), '</strong>'); ?>
	</p>
	<p>
		<em><?= __('Note') ?>:</em>
		<?= __('The comments field can be left empty. However, it is highly recommended to add a comment when rejecting a request.') ?>
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
				<label for="id_comments"><?= __("Comments") ?>:</label>
				<textarea name="comments" id="id_comments" rows="5" cols="50"></textarea>
			</p>
			<p>
				<input type="submit" class="button" name="do_CloseRequest" value="<?= __("Close Request") ?>" />
			</p>
		</fieldset>
	</form>
</div>

