<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once('aur.inc.php');         # access AUR common functions
include_once('acctfuncs.inc.php');   # access Account specific functions

set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in

html_header(__('Accounts'));

# Main page processing here
#
echo "<div class=\"box\">\n";
echo "  <h2>".__("Accounts")."</h2>\n";

$action = in_request("Action");

if (isset($_COOKIE["AURSID"])) {
	# visitor is logged in
	#
	$dbh = db_connect();
	$atype = account_from_sid($_COOKIE["AURSID"]);

	if ($action == "SearchAccounts") {

		# security check
		#
		if ($atype == "Trusted User" || $atype == "Developer") {
			# the user has entered search criteria, find any matching accounts
			#
			search_results_page($atype, in_request("O"), in_request("SB"),
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
		$row = account_details(in_request("ID"), in_request("U"));
		if (empty($row)) {
			print __("Could not retrieve information for the specified user.");
		} else {
			# double check to make sure logged in user can edit this account
			#
			if ($atype == "User" || ($atype == "Trusted User" && $row["AccountType"] == "Developer")) {
				print __("You do not have permission to edit this account.");
			} else {

				display_account_form($atype, "UpdateAccount", $row["Username"],
						$row["AccountType"], $row["Suspended"], $row["Email"],
						"", "", $row["RealName"], $row["LangPreference"],
						$row["IRCNick"], $row["PGPKey"], $row["ID"]);
			}
		}

	} elseif ($action == "AccountInfo") {
		# no editing, just looking up user info
		#
		$row = account_details(in_request("ID"), in_request("U"));
		if (empty($row)) {
			print __("Could not retrieve information for the specified user.");
		} else {
			include("account_details.php");
		}

	} elseif ($action == "UpdateAccount") {
		# user is submitting their modifications to an existing account
		#
		process_account_form($atype, "edit", "UpdateAccount",
				in_request("U"), in_request("T"), in_request("S"),
				in_request("E"), in_request("P"), in_request("C"),
				in_request("R"), in_request("L"), in_request("I"),
				in_request("K"), in_request("ID"));


	} else {
		if ($atype == "Trusted User" || $atype == "Developer") {
			# display the search page if they're a TU/dev
			#
			print __("Use this form to search existing accounts.")."<br />\n";
			search_accounts_form();

		} else {
			# A normal user, give them the ability to edit
			# their own account
			#
			$row = own_account_details($_COOKIE["AURSID"]);
			if (empty($row)) {
				print __("Could not retrieve information for the specified user.");
			} else {
				# don't need to check if they have permissions, this is a
				# normal user editing themselves.
				#
				print __("Use this form to update your account.");
				print "<br />";
				print __("Leave the password fields blank to keep your same password.");
				display_account_form($atype, "UpdateAccount", $row["Username"],
						$row["AccountType"], $row["Suspended"], $row["Email"],
						"", "", $row["RealName"], $row["LangPreference"],
						$row["IRCNick"], $row["PGPKey"], $row["ID"]);
			}
		}
	}

} else {
	# visitor is not logged in
	#
	if ($action == "AccountInfo") {
		print __("You must log in to view user information.");
	}	elseif ($action == "NewAccount") {
		# process the form input for creating a new account
		#
		process_account_form("","new", "NewAccount",
				in_request("U"), 1, 0, in_request("E"),
				in_request("P"), in_request("C"), in_request("R"),
				in_request("L"), in_request("I"), in_request("K"));

	} else {
		# display the account request form
		#
		print __("Use this form to create an account.");
		display_account_form("", "NewAccount");
	}
}

echo "</div>";

html_footer(AUR_VERSION);

?>
