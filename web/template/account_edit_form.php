<?php if ($A == "UpdateAccount"): ?>
<form action="<?= get_user_uri($U) . 'update/'; ?>" method="post">
<?php else: ?>
<form action="<?= get_uri('/register/'); ?>" method="post">
<?php endif; ?>
	<fieldset>
		<input type="hidden" name="Action" value="<?= $A ?>" />
		<?php if ($UID): ?>
		<input type="hidden" name="ID" value="<?= $UID ?>" />
		<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
		<?php endif; ?>
	</fieldset>
	<table>
		<tr>
			<td colspan="2">&nbsp;</td>
		</tr>

		<tr>
			<td align="left"><?= __("Username") ?>:</td>
			<td align="left"><input type="text" size="30" maxlength="64" name="U" value="<?= htmlspecialchars($U,ENT_QUOTES) ?>" /> (<?= __("required") ?>)</td>
		</tr>
		<?php
		# Only TUs or Devs can promote/demote/suspend a user
		if ($UTYPE == "Trusted User" || $UTYPE == "Developer"):
		?>
		<tr>
			<td align="left"><?= __("Account Type") ?>:</td>
			<td align="left">
				<select name=T>
					<?php if ($T == "User"): ?>
					<option value="1" selected><?= __("Normal user") ?>
					<?php else: ?>
					<option value="1"><?= __("Normal user") ?>
					<?php endif; ?>
					<?php if ($T == "Trusted User"): ?>
					<option value="2" selected><?= __("Trusted user") ?>
					<?php else: ?>
					<option value="2"><?= __("Trusted user") ?>
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
			<td align="left"><?= __("Account Suspended") ?>:</td>

			<?php if ($S): ?>
			<td align="left"><input type="checkbox" name="S" checked="checked" />
			<?php else: ?>
			<td align="left"><input type="checkbox" name="S" />
			<?php endif; ?>
		</tr>
		<?php endif; ?>

		<tr>
			<td align="left"><?= __("Email Address") ?>:</td>
			<td align="left"><input type="text" size="30" maxlength="64" name="E" value="<?= htmlspecialchars($E,ENT_QUOTES) ?>" /> (<?= __("required") ?>)</td>
		</tr>

		<tr>
			<td align="left"><?= __("Password") ?>:</td>
			<td align="left">
				<input type="password" size="30" maxlength="32" name="P" value="<?= $P ?>" />
				<?php if ($A != "UpdateAccount"):
					print " (".__("required").")";
				endif; ?>
			</td>
		</tr>

		<tr>
			<td align="left"><?= __("Re-type password") ?>:</td>
			<td align="left">
				<input type="password" size="30" maxlength="32" name="C" value="<?= $C ?>" />
				<?php if ($A != "UpdateAccount"):
					print " (".__("required").")";
				endif; ?>
			</td>
		</tr>

		<tr>
			<td align="left"><?= __("Real Name") ?>:</td>
			<td align="left">
				<input type="text" size="30" maxlength="32" name="R" value="<?= htmlspecialchars($R,ENT_QUOTES) ?>" />
			</td>
		</tr>

		<tr>
			<td align="left"><?= __("IRC Nick") ?>:</td>
			<td align="left">
				<input type="text" size="30" maxlength="32" name="I" value="<?= htmlspecialchars($I,ENT_QUOTES) ?>" />
			</td>
		</tr>

		<tr>
			<td align="left"><?= __("PGP Key Fingerprint") ?>:</td>
<td align="left">
				<input type="text" size="30" maxlength="50" name="K" value="<?= html_format_pgp_fingerprint($K) ?>" />
			</td>
		</tr>

		<tr>
			<td align="left"><?= __("Language") ?>:</td>
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
				<input type="submit" class="button" value="<?= __("Update") ?>" /> &nbsp;
				<?php else: ?>
				<input type="submit" class="button" value="<?= __("Create") ?>" /> &nbsp;
				<?php endif; ?>
				<input type="reset" class="button" value="<?= __("Reset") ?>" />
			</td>
		</tr>

	</table>
</form>
