<?php if ($A == "UpdateAccount"): ?>
<form id="edit-profile-form" action="<?= get_user_uri($U) . 'update/'; ?>" method="post">
<?php else: ?>
<form id="edit-profile-form" action="<?= get_uri('/register/'); ?>" method="post">
<?php endif; ?>
	<fieldset>
		<input type="hidden" name="Action" value="<?= $A ?>" />
		<?php if ($UID): ?>
		<input type="hidden" name="ID" value="<?= $UID ?>" />
		<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
		<?php endif; ?>
	</fieldset>
	<fieldset>
		<p>
			<label for="id_username"><?= __("Username") ?>:</label>
			<input type="text" size="30" maxlength="64" name="U" id="id_username" value="<?= htmlspecialchars($U,ENT_QUOTES) ?>" /> (<?= __("required") ?>)
		</p>
		<?php
		# Only TUs or Devs can promote/demote/suspend a user
		if ($UTYPE == "Trusted User" || $UTYPE == "Developer"):
		?>
		<p>
			<label for="id_type"><?= __("Account Type") ?>:</label>
			<select name="T" id="id_type">
				<?php if ($T == 1): ?>
				<option value="1" selected="selected"><?= __("Normal user") ?></option>
				<?php else: ?>
				<option value="1"><?= __("Normal user") ?></option>
				<?php endif; ?>
				<?php if ($T == 2): ?>
				<option value="2" selected="selected"><?= __("Trusted user") ?></option>
				<?php else: ?>
				<option value="2"><?= __("Trusted user") ?></option>
				<?php endif; ?>
				<?php
				# Only developers can make another account a developer
				if ($UTYPE == "Developer"):
				?>
				<option value="3"
				<?php $T == 3 ? print " selected=\"selected\">" : print ">";
				print __("Developer")."\n"; ?>
				</option>
				<?php endif; ?>

			</select>
		</p>

		<p>
			<label for="id_suspended"><?= __("Account Suspended") ?>:</label>
			<?php if ($S): ?>
			<input type="checkbox" name="S" id="id_suspended" checked="checked" />
			<?php else: ?>
			<input type="checkbox" name="S" id="id_suspended" />
			<?php endif; ?>
		</p>
		<?php endif; ?>

		<p>
			<label for="id_inactive"><?= __("Inactive") ?>:</label>
			<input type="checkbox" name="J" id="id_inactive" <?= $J ? 'checked="checked"' : '' ?> />
		</p>

		<p>
			<label for="id_email"><?= __("Email Address") ?>:</label>
			<input type="text" size="30" maxlength="64" name="E" id="id_email" value="<?= htmlspecialchars($E,ENT_QUOTES) ?>" /> (<?= __("required") ?>)
		</p>

		<?php if ($A == "UpdateAccount"): ?>
		<p>
			<label for="id_passwd1"><?= __("Password") ?>:</label>
			<input type="password" size="30" name="P" id="id_passwd1" value="<?= $P ?>" />
		</p>

		<p>
			<label for="id_passwd2"><?= __("Re-type password") ?>:</label>
			<input type="password" size="30" name="C" id="id_passwd2" value="<?= $C ?>" />
		</p>
		<?php endif; ?>

		<p>
			<label for="id_realname"><?= __("Real Name") ?>:</label>
			<input type="text" size="30" maxlength="32" name="R" id="id_realname" value="<?= htmlspecialchars($R,ENT_QUOTES) ?>" />
		</p>

		<p>
			<label for="id_irc"><?= __("IRC Nick") ?>:</label>
			<input type="text" size="30" maxlength="32" name="I" id="id_irc" value="<?= htmlspecialchars($I,ENT_QUOTES) ?>" />
		</p>

		<p>
			<label for="id_pgp"><?= __("PGP Key Fingerprint") ?>:</label>
			<input type="text" size="30" maxlength="50" name="K" id="id_pgp" value="<?= html_format_pgp_fingerprint($K) ?>" />
		</p>

		<p>
			<label for="id_language"><?= __("Language") ?>:</label>
			<select name="L" id="id_language">
<?php
	reset($SUPPORTED_LANGS);
	while (list($code, $lang) = each($SUPPORTED_LANGS)) {
		if ($L == $code) {
			print "<option value=\"".$code."\" selected=\"selected\"> ".$lang."</option>"."\n";
		} else {
			print "<option value=\"".$code."\"> ".$lang."</option>"."\n";
		}
	}
?>
			</select>
		</p>

		<p>
			<label></label>
			<?php if ($A == "UpdateAccount"): ?>
			<input type="submit" class="button" value="<?= __("Update") ?>" /> &nbsp;
			<?php else: ?>
			<input type="submit" class="button" value="<?= __("Create") ?>" /> &nbsp;
			<?php endif; ?>
			<input type="reset" class="button" value="<?= __("Reset") ?>" />
		</p>
	</fieldset>
</form>
