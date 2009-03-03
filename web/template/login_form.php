<div id="login_bar">
<?php
if (isset($_COOKIE["AURSID"])) {
	print __("Logged-in as: %s", '<b>' . username_from_sid($_COOKIE["AURSID"]) . '</b>');
?>
 <a href="logout.php">[<?php print __("Logout"); ?>]</a>
<?php
}
else {
	if ($login_error) {
		print "<span class='error'>" . $login_error . "</span><br />\n";
	}
	 '?' . implode('&amp', $_GET);
?>
<form method="post" action="<?php echo $_SERVER['REQUEST_URI'] ?>">
	<div>
	<?php print __('Username') . ':'; ?>
	<input type="text" name="user" size="30" maxlength="<?php print USERNAME_MAX_LEN; ?>" value="<?php
	if (isset($_POST['user'])) {
		print htmlspecialchars($_POST['user'], ENT_QUOTES);
	} ?>" />
	<?php print __('Password') . ':'; ?>
	<input type="password" name="passwd" size="30" maxlength="<?php print PASSWD_MAX_LEN; ?>" />
	<input type="checkbox" name="remember_me" /><?php print __("Remember me"); ?>
	<input type="submit" class="button" value="<?php  print __("Login"); ?>" />
	</div>
</form>
<?php } ?>
</div>

