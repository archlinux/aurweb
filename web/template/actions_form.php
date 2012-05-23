<div class="box">
	<form action="packages.php?ID=<?php echo $row['ID'] ?>" method="post">
		<fieldset>
			<input type="hidden" name="IDs[<?php echo $row['ID'] ?>]" value="1" />
			<input type="hidden" name="ID" value="<?php echo $row['ID'] ?>" />

		<?php if (user_voted($uid, $row['ID'])): ?>
			<input type="submit" class="button" name="do_UnVote" value="<?php echo __("UnVote") ?>" />
		<?php else: ?>
			<input type="submit" class="button" name="do_Vote" value="<?php echo __("Vote") ?>" />
		<?php endif; ?>

		<?php if (user_notify($uid, $row['ID'])): ?>
			<input type="submit" class="button" name="do_UnNotify" value="<?php echo __("UnNotify") ?>" title="<?php echo __("No New Comment Notification") ?>" />
		<?php else: ?>
			<input type="submit" class="button" name="do_Notify" value="<?php echo __("Notify") ?>" title="<?php echo __("New Comment Notification") ?>" />
		<?php endif; ?>

		<?php if ($row["OutOfDateTS"] === NULL): ?>
			<input type="submit" class="button" name="do_Flag" value="<?php echo __("Flag Out-of-date") ?>" />
		<?php else: ?>
			<input type="submit" class="button" name="do_UnFlag" value="<?php echo __("UnFlag Out-of-date") ?>" />
		<?php endif; ?>
			
		<?php if ($row["MaintainerUID"] === NULL): ?>
			<input type="submit" class="button" name="do_Adopt" value="<?php echo __("Adopt Packages") ?>" />
		<?php elseif ($uid == $row["MaintainerUID"] ||
			$atype == "Trusted User" || $atype == "Developer"): ?>
			<input type="submit" class="button" name="do_Disown" value="<?php echo __("Disown Packages") ?>" />
		<?php endif; ?>

		<?php if ($atype == "Trusted User" || $atype == "Developer"): ?>
			<input type="submit" class="button" name="do_Delete" value="<?php echo __("Delete Packages") ?>" />
			<label for="merge_Into" ><?php echo __("Merge into") ?></label>
			<input type="text" id="merge_Into" name="merge_Into" />
			<input type="checkbox" name="confirm_Delete" value="1" />
			<?php echo __("Confirm") ?>
		<?php endif; ?>

		</fieldset>
	</form>
</div>
