<?php
# Now present the user login stuff
if (!isset($_COOKIE["AURSID"])):

	# the user is not logged in, give them login widgets
	#
	if (!empty($login['error'])) {
		print '<div class="error">' . $login['error']
			. '</div>';
	}
?>

	<form action="<?php print $_SERVER['PHP_SELF']; ?>" method="post">
	<label class="lbox"><?php print __("Username"); ?><br />
	<input type="text" name="user" size="30"
	 maxlength="<?php print USERNAME_MAX_LEN;?>"></label>

	<label class="lbox"><?php print  __("Password"); ?><br />
	<input type="password" name="passwd" size="30"
	 maxlength="<?php print PASSWD_MAX_LEN; ?>"></label>
	<br />
	<input type="submit" class="button"
	value="<?php print __("Login"); ?>">
	</form>

<?php 
else:
	print __("Logged-in as: %h%s%h",
		array("<b>", username_from_sid($_COOKIE["AURSID"]), "</b>"));
endif; 

# vim: ts=2 sw=2 noet ft=php
?>
