<?php if ($A == "UpdateAccount"): ?>
<p>
	<?= __('Click %shere%s if you want to permanently delete this account.', '<a href="' . get_user_uri($N) . 'delete/' . '">', '</a>') ?>
	<?= __('Click %shere%s for user details.', '<a href="' . get_user_uri($N) . '">', '</a>') ?>
</p>

<form id="edit-profile-form" action="<?= get_user_uri($N) . 'update/'; ?>" method="post">
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
			<input type="text" size="30" maxlength="<?= config_get_int('options', 'username_max_len'); ?>" name="U" id="id_username" value="<?= htmlspecialchars($U,ENT_QUOTES) ?>" /> (<?= __("required") ?>)
		</p>
		<?php
		# Only TUs or Devs can promote/demote/suspend a user
		if (has_credential(CRED_ACCOUNT_CHANGE_TYPE)):
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
				<?php if (has_credential(CRED_ACCOUNT_EDIT_DEV)): ?>
				<option value="3"
				<?php $T == 3 ? print " selected=\"selected\">" : print ">";
				print __("Developer")."\n"; ?>
				</option>
				<option value="4"
				<?php $T == 4 ? print " selected=\"selected\">" : print ">";
				print __("Trusted User & Developer")."\n"; ?>
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

		<?php if ($A == "UpdateAccount"): ?>
		<p>
			<label for="id_inactive"><?= __("Inactive") ?>:</label>
			<input type="checkbox" name="J" id="id_inactive" <?= $J ? 'checked="checked"' : '' ?> />
		</p>
		<?php endif; ?>

		<p>
			<label for="id_email"><?= __("Email Address") ?>:</label>
			<input type="text" size="30" maxlength="254" name="E" id="id_email" value="<?= htmlspecialchars($E,ENT_QUOTES) ?>" /> (<?= __("required") ?>)
		</p>

		<p>
			<em><?= __("Please ensure you correctly entered your email address, otherwise you will be locked out.") ?></em>
		</p>

		<p>
			<label for="id_hide"><?= __("Hide Email Address") ?>:</label>
			<input type="checkbox" name="H" id="id_hide" <?= $H ? 'checked="checked"' : '' ?> />
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
			<label for="id_homepage"><?= __("Homepage") ?>:</label>
			<input type="text" size="30" name="HP" id="id_homepage" value="<?= htmlspecialchars($HP,ENT_QUOTES) ?>" />
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
			<label for="id_timezone"><?= __("Timezone") ?></label>
			<select name="TZ" id="id_timezone">
<?php
	$timezones = generate_timezone_list();
	while (list($key, $val) = each($timezones)) {
		if ($TZ == $key) {
			print "<option value=\"".$key."\" selected=\"selected\"> ".$val."</option>\n";
		} else {
			print "<option value=\"".$key."\"> ".$val."</option>\n";
		}
	}
?>
			</select>
		</p>
	</fieldset>

	<fieldset>
		<legend><?= __("The following information is only required if you want to submit packages to the Arch User Repository.") ?></legend>
		<p>
			<label for="id_ssh"><?= __("SSH Public Key") ?>:</label>
			<textarea name="PK" id="id_ssh" rows="5" cols="30"><?= htmlspecialchars($PK) ?></textarea>
		</p>
	</fieldset>

	<fieldset>
		<legend><?= __("Notification settings") ?>:</legend>
		<p>
			<label for="id_commentnotify"><?= __("Notify of new comments") ?>:</label>
			<input type="checkbox" name="CN" id="id_commentnotify" <?= $CN ? 'checked="checked"' : '' ?> />
		</p>
		<p>
			<label for="id_updatenotify"><?= __("Notify of package updates") ?>:</label>
			<input type="checkbox" name="UN" id="id_updatenotify" <?= $UN ? 'checked="checked"' : '' ?> />
		</p>
		<p>
			<label for="id_ownershipnotify"><?= __("Notify of ownership changes") ?>:</label>
			<input type="checkbox" name="ON" id="id_ownershipnotify" <?= $ON ? 'checked="checked"' : '' ?> />
		</p>
	</fieldset>

	<fieldset>
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
