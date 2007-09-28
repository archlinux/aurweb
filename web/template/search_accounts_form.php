<br />
<form action='account.php' method='post'>
<input type='hidden' name='Action' value='SearchAccounts'>
<center>
<table border='0' cellpadding='0' cellspacing='0' width='80%'>

<tr>
	<td align='left'><?php print __("Username"); ?>:</td>
<td align='left'><input type='text' size='30' maxlength='64'
 name='U'></td>
</tr>

<tr>
<td align='left'><?php print __("Account Type"); ?>:</td>
<td align='left'><select name=T>
<option value=''><?php print __("Any type"); ?>
<option value='u'><?php print __("Normal user"); ?>
<option value='t'><?php print __("Trusted user"); ?>
<option value='d'><?php print __("Developer"); ?>
</select></td>
</tr>

<tr>
<td align='left'><?php print __("Account Suspended"); ?>:</td>
<td align='left'><input type='checkbox' name='S'>
</tr>

<tr>
<td align='left'><?php print __("Email Address"); ?>:</td>
<td align='left'><input type='text' size='30' maxlength='64'
 name='E'></td>
</tr>

<tr>
<td align='left'><?php print __("Real Name"); ?>:</td>
<td align='left'><input type='text' size='30' maxlength='32'
 name='R'></td>
</tr>

<tr>
<td align='left'><?php print __("IRC Nick"); ?>:</td>
<td align='left'><input type='text' size='30' maxlength='32'
 name='I'></td>
</tr>

<tr>
<td align='left'><?php print __("Sort by"); ?>:</td>
<td align='left'><select name=SB>
<option value='u'><?php print __("Username"); ?>
<option value='t'><?php print __("Account Type"); ?>
<option value='r'><?php print __("Real Name"); ?>
<option value='i'><?php print __("IRC Nick"); ?>
<option value='v'><?php print __("Last vote"); ?>
</select></td>
</tr>

<tr>
<td>&nbsp;</td>
<td align='left'>&nbsp;<br/>
<input type='submit' class='button'
	value="<?php print __("Search'"); ?>">
<input type='reset' class='button'
	value="<?php print __("Reset"); ?>"></td>
</tr>

</table>
</center>
</form>
