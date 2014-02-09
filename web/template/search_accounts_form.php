<br />
<form action="<?= get_uri('/accounts/'); ?>" method="post">
	<table>

		<tr>
			<td align="left"><?= __("Username"); ?>:</td>
			<td align="left">
				<input type="text" size="30" maxlength="64" name="U" />
			</td>
		</tr>

		<tr>
			<td align="left"><?= __("Account Type"); ?>:</td>
			<td align="left">
				<select name="T">
					<option value=""><?= __("Any type"); ?></option>
					<option value="u"><?= __("Normal user"); ?></option>
					<option value="t"><?= __("Trusted user"); ?></option>
					<option value="d"><?= __("Developer"); ?></option>
				</select>
			</td>
		</tr>

		<tr>
			<td align="left"><?= __("Account Suspended"); ?>:</td>
			<td align="left">
				<input type="checkbox" name="S" />
			</td>
		</tr>

		<tr>
			<td align="left"><?= __("Email Address"); ?>:</td>
			<td align="left">
				<input type="text" size="30" maxlength="64" name="E" />
			</td>
		</tr>

		<tr>
			<td align="left"><?= __("Real Name"); ?>:</td>
			<td align="left">
				<input type="text" size="30" maxlength="32" name="R" />
			</td>
		</tr>

		<tr>
			<td align="left"><?= __("IRC Nick"); ?>:</td>
			<td align="left">
				<input type="text" size="30" maxlength="32" name="I" />
			</td>
		</tr>

		<tr>
			<td align="left"><?= __("Sort by"); ?>:</td>
			<td align="left">
				<select name="SB">
					<option value="u"><?= __("Username"); ?></option>
					<option value="t"><?= __("Account Type"); ?></option>
					<option value="r"><?= __("Real Name"); ?></option>
					<option value="i"><?= __("IRC Nick"); ?></option>
				</select>
			</td>
		</tr>

		<tr>
			<td>&nbsp;</td>
			<td align="left">
				<br />
				<input type="hidden" name="Action" value="SearchAccounts" />
				<input type="submit" class="button" value="<?= __("Search"); ?>" />
				<input type="reset" class="button" value="<?= __("Reset"); ?>" />
			</td>
		</tr>

	</table>
</form>
