<?
include("aur.inc");         # access AUR common functions
include("acctfuncs.inc");   # access Account specific functions
include("account_po.inc");  # use some form of this for i18n support
set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in
html_header();              # print out the HTML header


# Main page processing here
#
if (isset($_COOKIE["AURSID"])) {
	# visitor is logged in
	#
	$dbh = db_connect();
	$atype = account_from_sid($_COOKIE["AURSID"]);

	if ($_REQUEST["Action"] == "SearchAccounts") {

		# security check
		#
		if ($atype == "Trusted user" || $atype == "Developer") {
			# the user has entered search criteria, find any matching accounts
			#
			search_results_page($_REQUEST["O"], $_REQUEST["SB"],
					$_REQUEST["U"], $_REQUEST["T"], $_REQUEST["S"],
					$_REQUEST["E"], $_REQUEST["R"], $_REQUEST["I"]);

		} else {
			# a non-privileged user is trying to access the search page
			#
			print __("You are not allowed to access this area.")."<br/>\n";
		}

	} elseif ($_REQUEST["Action"] == "DisplayAccount") {
		# the user has clicked 'edit', display the account details in a form
		#

	} elseif ($_REQUEST["Action"] == "UpdateAccount") {
		# user is submitting their modifications to an existing account
		#

	} else {
		if ($atype == "Trusted user" || $atype == "Developer") {
			# display the search page if they're a TU/dev
			#
			print __("Use this form to search existing accounts.")."<br/>\n";
			search_accounts_form();

		} else {
			# TODO A normal user, give them the ability to edit
			# their own account
			#
			print __("Regular users can edit their own account.");
		}
	}

} else {
	# visitor is not logged in
	#
	if ($_REQUEST["Action"] == "NewAccount") {
		# process the form input for creating a new account
		#
		process_account_form("","new", "NewAccount",
				$_REQUEST["U"], 1, 0, $_REQUEST["E"],
				$_REQUEST["P"], $_REQUEST["C"], $_REQUEST["R"],
				$_REQUEST["L"], $_REQUEST["I"], $_REQUEST["N"]);

	} else {
		# display the account request form
		#
		display_account_form("", "NewAccount");
	}
}

html_footer("\$Id$");
# vim: ts=2 sw=2 noet ft=php
?>
