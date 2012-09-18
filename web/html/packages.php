<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");      # access AUR common functions
set_lang();                       # this sets up the visitor's language
include_once('pkgfuncs.inc.php'); # package specific functions
check_sid();                      # see if they're still logged in

# Retrieve package ID and name, unless initialized by the routing framework
if (!isset($pkgid) || !isset($pkgname)) {
	if (isset($_GET['ID'])) {
		$pkgid = intval($_GET['ID']);
		$pkgname = pkgname_from_id($_GET['ID']);
	} else if (isset($_GET['N'])) {
		$pkgid = pkgid_from_name($_GET['N']);
		$pkgname = $_GET['N'];
	} else {
		unset($pkgid, $pkgname);
	}
}

# Set the title to the current query if required
if (isset($pkgname)) {
	$title = $pkgname;
} else if (!empty($_GET['K'])) {
	$title = __("Search Criteria") . ": " . $_GET['K'];
} else {
	$title = __("Packages");
}

# Retrieve account type
if (isset($_COOKIE["AURSID"])) {
	$atype = account_from_sid($_COOKIE["AURSID"]);
} else {
	$atype = "";
}

# Grab the list of Package IDs to be operated on
$ids = array();
if (isset($_POST['IDs'])) {
	foreach ($_POST['IDs'] as $id => $i) {
		$id = intval($id);
		if ($id > 0) {
			$ids[] = $id;
		}
	}
}

# Determine what action to do
$output = "";
if (check_token()) {
	if (current_action("do_Flag")) {
		$output = pkg_flag($atype, $ids, true);
	} elseif (current_action("do_UnFlag")) {
		$output = pkg_flag($atype, $ids, False);
	} elseif (current_action("do_Adopt")) {
		$output = pkg_adopt($atype, $ids, true);
	} elseif (current_action("do_Disown")) {
		$output = pkg_adopt($atype, $ids, False);
	} elseif (current_action("do_Vote")) {
		$output = pkg_vote($atype, $ids, true);
	} elseif (current_action("do_UnVote")) {
		$output = pkg_vote($atype, $ids, False);
	} elseif (current_action("do_Delete")) {
		if (isset($_POST['confirm_Delete'])) {
			if (!isset($_POST['merge_Into']) || empty($_POST['merge_Into'])) {
				$output = pkg_delete($atype, $ids, NULL);
				unset($_GET['ID']);
			}
			else {
				$mergepkgid = pkgid_from_name($_POST['merge_Into']);
				if ($mergepkgid) {
					$output = pkg_delete($atype, $ids, $mergepkgid);
					unset($_GET['ID']);
				}
				else {
					$output = __("Cannot find package to merge votes and comments into.");
				}
			}
		}
		else {
			$output = __("The selected packages have not been deleted, check the confirmation checkbox.");
		}
	} elseif (current_action("do_Notify")) {
		$output = pkg_notify($atype, $ids);
	} elseif (current_action("do_UnNotify")) {
		$output = pkg_notify($atype, $ids, False);
	} elseif (current_action("do_DeleteComment")) {
		$output = pkg_delete_comment($atype);
	} elseif (current_action("do_ChangeCategory")) {
		$output = pkg_change_category($atype);
	}
}

html_header($title);
?>

<?php if ($output): ?>
	<p class="pkgoutput"><?php print $output ?></p>
<?php endif; ?>

<?php
if (isset($pkgid)) {
	include('pkg_search_form.php');
	if ($pkgid) {
		if (isset($_COOKIE["AURSID"])) {
			package_details($pkgid, $_COOKIE["AURSID"]);
		}
		else {
			package_details($pkgid, null);
		}
	} else {
		print __("Error trying to retrieve package details.")."<br />\n";
	}
} else {
	if (!isset($_GET['K']) && !isset($_GET['SB'])) {
		$_GET['SB'] = 'v';
		$_GET['SO'] = 'd';
	}
	if (isset($_COOKIE["AURSID"])) {
		pkg_search_page($_COOKIE["AURSID"]);
	} else {
		pkg_search_page();
	}
}

html_footer(AUR_VERSION);

