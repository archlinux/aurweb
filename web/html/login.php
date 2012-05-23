<?php
set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
set_lang();
check_sid();

if (!$DISABLE_HTTP_LOGIN || (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'])) {
	$login = try_login();
	$login_error = $login['error'];
}

html_header('AUR ' . __("Login"));
?>
<div id="dev-login" class="box">
	<h2>AUR <?php echo __('Login') ?></h2>
	<?php if (isset($_COOKIE["AURSID"])): ?>
	<p>
		<?php echo __("Logged-in as: %s", '<strong>' . username_from_sid($_COOKIE["AURSID"]) . '</strong>'); ?>
		<a href="logout.php">[<?php print __("Logout"); ?>]</a>
	</p>
	<?php elseif (!$DISABLE_HTTP_LOGIN || (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'])): ?>
	<form method="post" action="<?php echo htmlspecialchars($_SERVER['REQUEST_URI'], ENT_QUOTES) ?>">
		<fieldset>
			<legend><?php echo __('Enter login credentials') ?></legend>
			<?php if (!empty($login_error)): ?>
			<ul class="errorlist"><li><?php echo $login_error ?></li></ul>
			<?php endif; ?>
			<p>
				<label for="id_username"><?php print __('Username') . ':'; ?></label>
				<input id="id_username" type="text" name="user" size="30" maxlength="<?php print USERNAME_MAX_LEN; ?>" value="<?php if (isset($_POST['user'])) { print htmlspecialchars($_POST['user'], ENT_QUOTES); } ?>" />
			</p>
			<p>
				<label for="id_password"><?php print __('Password') . ':'; ?></label>
				<input id="id_password" type="password" name="passwd" size="30" maxlength="<?php print PASSWD_MAX_LEN; ?>" />
			</p>
			<p>
				<input type="checkbox" name="remember_me" id="id_remember_me" />
				<label for="id_remember_me"><?php print __("Remember me"); ?></label>
			</p>
			<p>
				<input type="submit" class="button" value="<?php  print __("Login"); ?>" />
				<a href="passreset.php">[<?php echo __('Forgot Password') ?>]</a>
			</p>
		</fieldset>
	</form>
	<?php else: ?>
	<p>
		<?php printf(__("HTTP login is disabled. Please %sswitch to HTTPs%s if you want to login."),
			'<a href="' . $AUR_LOCATION . htmlspecialchars($_SERVER['REQUEST_URI'], ENT_QUOTES) . '">', '</a>'); ?>
	</p>
	<?php endif; ?>
</div>
<?php
html_footer(AUR_VERSION);
