<?php
set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
set_lang();
check_sid();

$disable_http_login = config_get_bool('options', 'disable_http_login');
if (!$disable_http_login || (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'])) {
	$login = try_login();
	$login_error = $login['error'];
}

html_header('AUR ' . __("Login"));
?>
<div id="dev-login" class="box">
	<h2>AUR <?= __('Login') ?></h2>
	<?php if (isset($_COOKIE["AURSID"])): ?>
	<p>
		<?= __("Logged-in as: %s", '<strong>' . username_from_sid($_COOKIE["AURSID"]) . '</strong>'); ?>
		<a href="<?= get_uri('/logout/'); ?>">[<?= __("Logout"); ?>]</a>
	</p>
	<?php elseif (!$disable_http_login || (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'])): ?>
	<form method="post" action="<?= get_uri('/login') ?>">
		<fieldset>
			<legend><?= __('Enter login credentials') ?></legend>
			<?php if (!empty($login_error)): ?>
			<ul class="errorlist"><li><?= $login_error ?></li></ul>
			<?php endif; ?>
			<p>
				<label for="id_username"><?= __('Username') . ':'; ?></label>
				<input id="id_username" type="text" name="user" size="30" maxlength="<?= config_get_int('options', 'username_max_len'); ?>" value="<?php if (isset($_POST['user'])) { print htmlspecialchars($_POST['user'], ENT_QUOTES); } ?>" />
			</p>
			<p>
				<label for="id_password"><?= __('Password') . ':'; ?></label>
				<input id="id_password" type="password" name="passwd" size="30" />
			</p>
			<p>
				<input type="checkbox" name="remember_me" id="id_remember_me" />
				<label for="id_remember_me"><?= __("Remember me"); ?></label>
			</p>
			<p>
				<input type="submit" class="button" value="<?php  print __("Login"); ?>" />
				<a href="<?= get_uri('/passreset/') ?>">[<?= __('Forgot Password') ?>]</a>
			</p>
		</fieldset>
	</form>
	<?php else: ?>
	<p>
		<?php printf(__("HTTP login is disabled. Please %sswitch to HTTPs%s if you want to login."),
			'<a href="' . aur_location() . get_uri('/login') . '">', '</a>'); ?>
	</p>
	<?php endif; ?>
</div>
<?php
html_footer(AUR_VERSION);
