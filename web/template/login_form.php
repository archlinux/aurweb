<div id="login_bar" class="pgbox">
<?php
if (isset($_COOKIE["AURSID"])) {
	print __("Logged-in as: %s", '<b>' . username_from_sid($_COOKIE["AURSID"]) . '</b>');
?>
 <a href="logout.php">[<?php print __("Logout"); ?>]</a>
<?php
}
elseif (!$DISABLE_HTTP_LOGIN || (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'])) {
	if ($login_error) {
		print "<span class='error'>" . $login_error . "</span><br />\n";
	}
?>
<form method="post" action="<?php echo htmlspecialchars($_SERVER['REQUEST_URI'], ENT_QUOTES) ?>">
	<div>
	<label for="user"><?php print __('Username') . ':'; ?></label>
	<input type="text" name="user" id="user" size="30" maxlength="<?php print USERNAME_MAX_LEN; ?>" value="<?php
	if (isset($_POST['user'])) {
		print htmlspecialchars($_POST['user'], ENT_QUOTES);
	} ?>" />
	<label for="passwd"><?php print __('Password') . ':'; ?></label>
	<input type="password" name="passwd" id="passwd" size="30" maxlength="<?php print PASSWD_MAX_LEN; ?>" />
	<input type="checkbox" name="remember_me" id="remember_me" />
	<label for="remember_me"><?php print __("Remember me"); ?></label>
	<input type="submit" class="button" value="<?php  print __("Login"); ?>" />
	<a href="passreset.php">[<?php echo __('Forgot Password') ?>]</a>
	</div>
</form>
<?php
}
else {
?>
<span class='error'>
	<?php printf(__("HTTP login is disabled. Please %sswitch to HTTPs%s if you want to login."),
		'<a href="https://aur.archlinux.org' . htmlspecialchars($_SERVER['REQUEST_URI'], ENT_QUOTES) . '">', '</a>'); ?>
</span>
<?php } ?>
</div>
