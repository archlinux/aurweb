<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");         # access AUR common functions

set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in

if (isset($_COOKIE["AURSID"])) {
	header('Location: index.php');
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
	$uid = uid_from_email($email);
	if ($uid != NULL && $uid != 'None') {
		# We (ab)use new_sid() to get a random 32 characters long string
		$resetkey = new_sid();
		create_resetkey($resetkey, $uid);
		# Send email with confirmation link
		$body = __('A password reset request was submitted for the account '.
		           'associated with your e-mail address. If you wish to reset '.
		           'your password follow the link below, otherwise ignore '.
		           'this message and nothing will happen.').
		           "\n\n".
		           "{$AUR_LOCATION}/passreset.php?".
		           "resetkey={$resetkey}";
		$body = wordwrap($body, 70);
		$headers = "Reply-to: nobody@archlinux.org\nFrom:aur-notify@archlinux.org\nX-Mailer: PHP\nX-MimeOLE: Produced By AUR";
		@mail($email, 'AUR Password Reset', $body, $headers);

	}
	header('Location: passreset.php?step=confirm');
	exit();
}

$step = isset($_GET['step']) ? $_GET['step'] : NULL;

html_header(__("Password Reset"));

?>

<div class="box">
	<h2><?php print __("Password Reset"); ?></h2>

	<?php if ($error): ?>
		<p><span class="error"><?php echo $error ?></span></p>
	<?php endif;?>
	<?php
	if ($step == 'confirm') {
		echo __('Check your e-mail for the confirmation link.');
	} elseif ($step == 'complete') {
		echo __('Your password has been reset successfully.');
	} elseif (isset($_GET['resetkey'])) {
	?>
	<form action="" method="post">
		<table>
			<tr>
				<td><?php echo __("Confirm your e-mail address:"); ?></td>
				<td><input type="text" name="email" size="30" maxlength="64" /></td>
			</tr>
			<tr>
				<td><?php echo __("Enter your new password:"); ?></td>
				<td><input type="password" name="password" size="30" maxlength="32" /></td>
			</tr>
			<tr>
				<td><?php echo __("Confirm your new password:"); ?></td>
				<td><input type="password" name="confirm" size="30" maxlength="32" /></td>
			</tr>
		</table>
		<br />
		<input type="submit" class="button" value="<?php echo __('Continue') ?>" />
	</form>
	<?php
	} else {
	?>
	<p><?php echo __('If you have forgotten the e-mail address you used to register, please send a message to the %saur-general%s mailing list.',
	'<a href="http://mailman.archlinux.org/mailman/listinfo/aur-general">',
	'</a>'); ?></p>
	<form action="" method="post">
		<p><?php echo __("Enter your e-mail address:"); ?>
		<input type="text" name="email" size="30" maxlength="64" /></p>
		<input type="submit" class="button" value="<?php echo __('Continue') ?>" />
	</form>
	<?php } ?>
</div>

<?php

html_footer(AUR_VERSION);
