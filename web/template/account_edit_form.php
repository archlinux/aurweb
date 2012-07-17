<form action="<?php echo get_uri('/account/'); ?>" method="post">
	<fieldset>
		<input type="hidden" name="Action" value="<?php echo $A ?>" />
		<?php if ($UID): ?>
		<input type="hidden" name="ID" value="<?php echo $UID ?>" />
		<input type="hidden" name="token" value="<?php print htmlspecialchars($_COOKIE['AURSID']) ?>" />
		<?php endif; ?>
	</fieldset>
	<table>
		<tr>
			<td colspan="2">&nbsp;</td>
		</tr>

		<tr>
			<td align="left"><?php echo __("Username") ?>:</td>
			<td align="left"><input type="text" size="30" maxlength="64" name="U" value="<?php echo htmlspecialchars($U,ENT_QUOTES) ?>" /> (<?php echo __("required") ?>)</td>
		</tr>
		<?php
		# Only TUs or Devs can promote/demote/suspend a user
		if ($UTYPE == "Trusted User" || $UTYPE == "Developer"):
		?>
		<tr>
			<td align="left"><?php echo __("Account Type") ?>:</td>
			<td align="left">
				<select name=T>
					<?php if ($T == "User"): ?>
					<option value="1" selected><?php echo __("Normal user") ?>
					<?php else: ?>
					<option value="1"><?php echo __("Normal user") ?>
					<?php endif; ?>
					<?php if ($T == "Trusted User"): ?>
					<option value="2" selected><?php echo __("Trusted user") ?>
					<?php else: ?>
					<option value="2"><?php echo __("Trusted user") ?>
					<?php endif; ?>
					<?php
					# Only developers can make another account a developer
					if ($UTYPE == "Developer"):
					?>
					<option value="3"
					<?php $T == "Developer" ? print " selected>" : print ">";
					print __("Developer")."\n"; ?>
					<?php endif; ?>
				</select>
			</td>
		</tr>

		<tr>
			<td align="left"><?php echo __("Account Suspended") ?>:</td>

			<?php if ($S): ?>
			<td align="left"><input type="checkbox" name="S" checked="checked" />
			<?php else: ?>
			<td align="left"><input type="checkbox" name="S" />
			<?php endif; ?>
		</tr>
		<?php endif; ?>

		<tr>
			<td align="left"><?php echo __("Email Address") ?>:</td>
			<td align="left"><input type="text" size="30" maxlength="64" name="E" value="<?php echo htmlspecialchars($E,ENT_QUOTES) ?>" /> (<?php echo __("required") ?>)</td>
		</tr>

		<tr>
			<td align="left"><?php echo __("Password") ?>:</td>
			<td align="left">
				<input type="password" size="30" maxlength="32" name="P" value="<?php echo $P ?>" />
				<?php if ($A != "UpdateAccount"):
					print " (".__("required").")";
				endif; ?>
			</td>
		</tr>

		<tr>
			<td align="left"><?php echo __("Re-type password") ?>:</td>
			<td align="left">
				<input type="password" size="30" maxlength="32" name="C" value="<?php echo $C ?>" />
				<?php if ($A != "UpdateAccount"):
					print " (".__("required").")";
				endif; ?>
			</td>
		</tr>

		<tr>
			<td align="left"><?php echo __("Real Name") ?>:</td>
			<td align="left">
				<input type="text" size="30" maxlength="32" name="R" value="<?php echo htmlspecialchars($R,ENT_QUOTES) ?>" />
			</td>
		</tr>

		<tr>
			<td align="left"><?php echo __("IRC Nick") ?>:</td>
			<td align="left">
				<input type="text" size="30" maxlength="32" name="I" value="<?php echo htmlspecialchars($I,ENT_QUOTES) ?>" />
			</td>
		</tr>

		<tr>
			<td align="left"><?php echo __("PGP Key Fingerprint") ?>:</td>
<td align="left">
				<input type="text" size="30" maxlength="50" name="K" value="<?php echo html_format_pgp_fingerprint($K) ?>" />
			</td>
		</tr>

		<tr>
			<td align="left"><?php echo __("Language") ?>:</td>
			<td align="left">
				<select name=L>
<?php
	reset($SUPPORTED_LANGS);
	while (list($code, $lang) = each($SUPPORTED_LANGS)) {
		if ($L == $code) {
			print "<option value=".$code." selected> ".$lang."\n";
		} else {
			print "<option value=".$code."> ".$lang."\n";
		}
	}
?>
				</select>
			</td>
		</tr>

		<tr>
			<td colspan="2">&nbsp;</td>
		</tr>
		<tr>
			<td>&nbsp;</td>
			<td align="left">
				<?php if ($A == "UpdateAccount"): ?>
				<input type="submit" class="button" value="<?php echo __("Update") ?>" /> &nbsp;
				<?php else: ?>
				<input type="submit" class="button" value="<?php echo __("Create") ?>" /> &nbsp;
				<?php endif; ?>
				<input type="reset" class="button" value="<?php echo __("Reset") ?>" />
			</td>
		</tr>

	</table>
</form>
