<?php if (!use_virtual_urls()): ?>
<div class="box">
	<form action="<?= htmlspecialchars(get_pkg_uri($row['Name']), ENT_QUOTES); ?>" method="post">
		<fieldset>
			<input type="hidden" name="IDs[<?= $row['ID'] ?>]" value="1" />
			<input type="hidden" name="ID" value="<?= $row['ID'] ?>" />
			<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />

		<?php if (pkgbase_user_voted($uid, $row['ID'])): ?>
			<input type="submit" class="button" name="do_UnVote" value="<?= __("UnVote") ?>" />
		<?php else: ?>
			<input type="submit" class="button" name="do_Vote" value="<?= __("Vote") ?>" />
		<?php endif; ?>

		<?php if (pkgbase_user_notify($uid, $row['ID'])): ?>
			<input type="submit" class="button" name="do_UnNotify" value="<?= __("UnNotify") ?>" title="<?= __("No New Comment Notification") ?>" />
		<?php else: ?>
			<input type="submit" class="button" name="do_Notify" value="<?= __("Notify") ?>" title="<?= __("New Comment Notification") ?>" />
		<?php endif; ?>

		<?php if ($row["OutOfDateTS"] === NULL): ?>
			<input type="submit" class="button" name="do_Flag" value="<?= __("Flag Out-of-date") ?>" />
		<?php elseif (($row["OutOfDateTS"] !== NULL) && has_credential(CRED_PKGBASE_UNFLAG, array($row["MaintainerUID"]))): ?>
			<input type="submit" class="button" name="do_UnFlag" value="<?= __("UnFlag Out-of-date") ?>" />
		<?php endif; ?>
			
		<?php if (has_credential(CRED_PKGBASE_DELETE)): ?>
			<input type="submit" class="button" name="do_Delete" value="<?= __("Delete Packages") ?>" />
			<label for="merge_Into" ><?= __("Merge into") ?></label>
			<input type="text" id="merge_Into" name="merge_Into" />
			<input type="checkbox" name="confirm_Delete" value="1" />
			<?= __("Confirm") ?>
		<?php endif; ?>

		</fieldset>
	</form>
</div>
<?php endif; ?>
