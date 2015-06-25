<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once('aur.inc.php');         # access AUR common functions
include_once('acctfuncs.inc.php');   # access Account specific functions

set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in

$action = in_request("Action");

$need_userinfo = array(
	"DisplayAccount", "DeleteAccount", "AccountInfo", "UpdateAccount"
);

if (in_array($action, $need_userinfo)) {
	$row = account_details(in_request("ID"), in_request("U"));
}

if ($action == "AccountInfo") {
	html_header(__('Account') . ' ' . $row['Username']);
} else {
	html_header(__('Accounts'));
}

# Main page processing here
#
echo "<div class=\"box\">\n";
echo "  <h2>".__("Accounts")."</h2>\n";

if (isset($_COOKIE["AURSID"])) {
	if ($action == "SearchAccounts") {

		# security check
		#
		if (has_credential(CRED_ACCOUNT_SEARCH)) {
			# the user has entered search criteria, find any matching accounts
			#
			search_results_page(in_request("O"), in_request("SB"),
					in_request("U"), in_request("T"), in_request("S"),
					in_request("E"), in_request("R"), in_request("I"),
					in_request("K"));

		} else {
			# a non-privileged user is trying to access the search page
			#
			print __("You are not allowed to access this area.")."<br />\n";
		}

	} elseif ($action == "DisplayAccount") {
		# the user has clicked 'edit', display the account details in a form
		#
		if (empty($row)) {
			print __("Could not retrieve information for the specified user.");
		} else {
			/* Verify user has permission to edit the account */
			if (can_edit_account($row)) {
				display_account_form("UpdateAccount", $row["Username"],
					$row["AccountTypeID"], $row["Suspended"], $row["Email"],
					"", "", $row["RealName"], $row["LangPreference"],
					$row["IRCNick"], $row["PGPKey"], $row["SSHPubKey"],
					$row["InactivityTS"] ? 1 : 0, $row["ID"]);
			} else {
				print __("You do not have permission to edit this account.");
			}
		}

	} elseif ($action == "DeleteAccount") {
		/* Details for account being deleted. */
		if (can_edit_account($row)) {
			$UID = $row['ID'];
			if (in_request('confirm') && check_token()) {
				user_delete($UID);
				header('Location: /');
			} else {
				$username = $row['Username'];
				include("account_delete.php");
			}
		} else {
			print __("You do not have permission to edit this account.");
		}
	} elseif ($action == "AccountInfo") {
		# no editing, just looking up user info
		#
		if (empty($row)) {
			print __("Could not retrieve information for the specified user.");
		} else {
			include("account_details.php");
		}

	} elseif ($action == "UpdateAccount") {
		/* Details for account being updated */
		/* Verify user permissions and that the request is a valid POST */
		if (can_edit_account($row) && check_token()) {
			/* Update the details for the existing account */
			process_account_form("edit", "UpdateAccount",
					in_request("U"), in_request("T"), in_request("S"),
					in_request("E"), in_request("P"), in_request("C"),
					in_request("R"), in_request("L"), in_request("I"),
					in_request("K"), in_request("PK"), in_request("J"),
					in_request("ID"));
		}
	} else {
		if (has_credential(CRED_ACCOUNT_SEARCH)) {
			# display the search page if they're a TU/dev
			#
			print __("Use this form to search existing accounts.")."<br />\n";
			include('search_accounts_form.php');

		} else {
			print __("You are not allowed to access this area.");
		}
	}

} else {
	# visitor is not logged in
	#
	print __("You must log in to view user information.");
}

echo "</div>";

html_footer(AURWEB_VERSION);

?>
