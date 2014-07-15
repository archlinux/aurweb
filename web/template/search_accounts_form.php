<br />
<form action="<?= get_uri('/accounts/'); ?>" method="post">
	<fieldset>
		<input type="hidden" name="Action" value="SearchAccounts" />
	</fieldset>
	<fieldset>
		<p>
			<label for="id_username"><?= __("Username"); ?>:</label>
			<input type="text" size="30" maxlength="64" name="U" id="id_username" />
		</p>
		<p>
			<label for="id_type"><?= __("Account Type"); ?>:</label>
			<select name="T" id="id_type">
				<option value=""><?= __("Any type"); ?></option>
				<option value="u"><?= __("Normal user"); ?></option>
				<option value="t"><?= __("Trusted user"); ?></option>
				<option value="d"><?= __("Developer"); ?></option>
				<option value="td"><?= __("Trusted User & Developer"); ?></option>
			</select>
		</p>
		<p>
			<label for="id_suspended"><?= __("Account Suspended"); ?>:</label>
			<input type="checkbox" name="S" id="id_suspended" />
		</p>
		<p>
			<label for="id_email"><?= __("Email Address"); ?>:</label>
			<input type="text" size="30" maxlength="64" name="E" id="id_email" />
		</p>
		<p>
			<label for="id_realname"><?= __("Real Name"); ?>:</label>
			<input type="text" size="30" maxlength="32" name="R" id="id_realname" />
		</p>
		<p>
			<label for="id_irc"><?= __("IRC Nick"); ?>:</label>
			<input type="text" size="30" maxlength="32" name="I" id="id_irc" />
		</p>
		<p>
			<label for="id_sortby"><?= __("Sort by"); ?>:</label>
			<select name="SB" id="id_sortby">
				<option value="u"><?= __("Username"); ?></option>
				<option value="t"><?= __("Account Type"); ?></option>
				<option value="r"><?= __("Real Name"); ?></option>
				<option value="i"><?= __("IRC Nick"); ?></option>
			</select>
		</p>
		<p>
			<label></label>
			<input type="submit" class="button" value="<?= __("Search"); ?>" /> &nbsp;
			<input type="reset" class="button" value="<?= __("Reset"); ?>" />
		</p>
	</fieldset>
</form>
