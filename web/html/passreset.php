<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");         # access AUR common functions

set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in

if (isset($_COOKIE["AURSID"])) {
	header('Location: /');
	exit();
}

$error = '';

if (isset($_GET['resetkey'], $_POST['email'], $_POST['password'], $_POST['confirm'])) {
	$resetkey = $_GET['resetkey'];
	$email = $_POST['email'];
	$password = $_POST['password'];
	$confirm = $_POST['confirm'];
	$uid = uid_from_email($email);

	if (empty($email) || empty($password)) {
		$error = __('Missing a required field.');
	} elseif ($password != $confirm) {
		$error = __('Password fields do not match.');
	} elseif ($uid == NULL || $uid == 'None') {
		$error = __('Invalid e-mail.');
	}

	if (empty($error)) {
		$salt = generate_salt();
		$hash = salted_hash($password, $salt);

		$error = password_reset($hash, $salt, $resetkey, $email);
	}
} elseif (isset($_POST['email'])) {
	$email = $_POST['email'];

	if (empty($email)) {
		$error = __('Missing a required field.');
	} else {
		$body = __('A password reset request was submitted for the account '.
			   'associated with your e-mail address. If you wish to reset '.
			   'your password follow the link below, otherwise ignore '.
			   'this message and nothing will happen.').
		send_resetkey($email, $body);

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
	<p>Check your e-mail for the confirmation link.</p>
	<?php elseif ($step == 'complete'): ?>
	<p>Your password has been reset successfully.</p>
	<?php elseif (isset($_GET['resetkey'])): ?>
	<?php if ($error): ?>
	<ul class="errorlist"><li><?= $error ?></li></ul>
	<?php endif; ?>
	<form action="" method="post">
		<table>
			<tr>
				<td><?= __("Confirm your e-mail address:"); ?></td>
				<td><input type="text" name="email" size="30" maxlength="64" /></td>
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
		<p><?= __("Enter your e-mail address:"); ?>
		<input type="text" name="email" size="30" maxlength="64" /></p>
		<input type="submit" class="button" value="<?= __('Continue') ?>" />
	</form>
	<?php endif; ?>
</div>

<?php

html_footer(AUR_VERSION);
