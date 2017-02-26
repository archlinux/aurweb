<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once('aur.inc.php');         # access AUR common functions
include_once('acctfuncs.inc.php');   # access Account specific functions

set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in

if (isset($_COOKIE["AURSID"])) {
	header('Location: /');
	exit();
}

html_header(__('Register'));

echo '<div class="box">';
echo '<h2>' . __('Register') . '</h2>';

if (in_request("Action") == "NewAccount") {
	list($success, $message) = process_account_form(
		"new",
		"NewAccount",
		in_request("U"),
		1,
		0,
		in_request("E"),
		in_request("H"),
		'',
		'',
		in_request("R"),
		in_request("L"),
		in_request("TZ"),
		in_request("HP"),
		in_request("I"),
		in_request("K"),
		in_request("PK"),
		0,
		in_request("CN"),
		in_request("UN"),
		in_request("ON"));

	print $message;

	if (!$success) {
		display_account_form("NewAccount",
			in_request("U"),
			1,
			0,
			in_request("E"),
			in_request("H"),
			'',
			'',
			in_request("R"),
			in_request("L"),
			in_request("TZ"),
			in_request("HP"),
			in_request("I"),
			in_request("K"),
			in_request("PK"),
			0,
			in_request("CN"),
			in_request("UN"),
			in_request("ON"));
	}
} else {
	print '<p>' . __("Use this form to create an account.") . '</p>';
	display_account_form("NewAccount", "", "", "", "", "", "", "", "", $LANG);
}

echo '</div>';

html_footer(AURWEB_VERSION);

?>
