<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");         # access AUR common functions

if (isset($_COOKIE["AURSID"])) {
	header('Location: /');
	exit();
}

$error = '';

if (isset($_GET['resetkey'], $_POST['user'], $_POST['password'], $_POST['confirm'])) {
	$resetkey = $_GET['resetkey'];
	$user = $_POST['user'];
	$password = $_POST['password'];
	$confirm = $_POST['confirm'];
	$uid = uid_from_loginname($user);

	if (empty($user) || empty($password)) {
		$error = __('Missing a required field.');
	} elseif ($password != $confirm) {
		$error = __('Password fields do not match.');
	} elseif (!good_passwd($password)) {
		$length_min = config_get_int('options', 'passwd_min_len');
		$error = __("Your password must be at least %s characters.",
			$length_min);
	} elseif ($uid == null) {
		$error = __('Invalid e-mail.');
	}

	if (empty($error)) {
		$error = password_reset($password, $resetkey, $user);
	}
} elseif (isset($_POST['user'])) {
	$user = $_POST['user'];

	if (empty($user)) {
		$error = __('Missing a required field.');
	} else {
		send_resetkey($user);
		header('Location: ' . get_uri('/passreset/') . '?step=confirm');
		exit();
	}
}

$step = isset($_GET['step']) ? $_GET['step'] : NULL;

html_header(__("Password Reset"));

?>

<div class="box">
	<h2><?= __("Password Reset"); ?></h2>

	<?php if ($step == 'confirm'): ?>
	<p><?= __('Check your e-mail for the confirmation link.') ?></p>
	<?php elseif ($step == 'complete'): ?>
	<p><?= __('Your password has been reset successfully.') ?></p>
	<?php elseif (isset($_GET['resetkey'])): ?>
	<?php if ($error): ?>
	<ul class="errorlist"><li><?= $error ?></li></ul>
	<?php endif; ?>
	<form action="" method="post">
		<table>
			<tr>
				<td><?= __("Confirm your e-mail address:"); ?></td>
				<td><input type="text" name="user" size="30" maxlength="64" /></td>
			</tr>
			<tr>
				<td><?= __("Enter your new password:"); ?></td>
				<td><input type="password" name="password" size="30" /></td>
			</tr>
			<tr>
				<td><?= __("Confirm your new password:"); ?></td>
				<td><input type="password" name="confirm" size="30" /></td>
			</tr>
		</table>
		<br />
		<input type="submit" class="button" value="<?= __('Continue') ?>" />
	</form>
	<?php else: ?>
	<p><?= __('If you have forgotten the e-mail address you used to register, please send a message to the %saur-general%s mailing list.',
	'<a href="https://mailman.archlinux.org/mailman/listinfo/aur-general">',
	'</a>'); ?></p>
	<?php if ($error): ?>
	<ul class="errorlist"><li><?= $error ?></li></ul>
	<?php endif; ?>
	<form action="" method="post">
		<p><?= __("Enter your user name or your e-mail address:"); ?>
		<input type="text" name="user" size="30" maxlength="64" /></p>
		<input type="submit" class="button" value="<?= __('Continue') ?>" />
	</form>
	<?php endif; ?>
</div>

<?php

html_footer(AURWEB_VERSION);
