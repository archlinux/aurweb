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

	if (isset($pkgid) && ($pkgid == 0 || $pkgid == NULL || $pkgname == NULL)) {
		header("HTTP/1.0 404 Not Found");
		include "./404.php";
		return;
	}
}

# Set the title to the current query or package name
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
$ret = false;
$output = "";
if (check_token()) {
	if (current_action("do_Flag")) {
		list($ret, $output) = pkg_flag($atype, $ids);
	} elseif (current_action("do_UnFlag")) {
		list($ret, $output) = pkg_unflag($atype, $ids);
	} elseif (current_action("do_Adopt")) {
		list($ret, $output) = pkg_adopt($atype, $ids, true);
	} elseif (current_action("do_Disown")) {
		list($ret, $output) = pkg_adopt($atype, $ids, False);
	} elseif (current_action("do_Vote")) {
		list($ret, $output) = pkg_vote($atype, $ids, true);
	} elseif (current_action("do_UnVote")) {
		list($ret, $output) = pkg_vote($atype, $ids, False);
	} elseif (current_action("do_Delete")) {
		if (isset($_POST['confirm_Delete'])) {
			if (!isset($_POST['merge_Into']) || empty($_POST['merge_Into'])) {
				list($ret, $output) = pkg_delete($atype, $ids, NULL);
				unset($_GET['ID']);
			}
			else {
				$mergepkgid = pkgid_from_name($_POST['merge_Into']);
				if ($mergepkgid) {
					list($ret, $output) = pkg_delete($atype, $ids, $mergepkgid);
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
		list($ret, $output) = pkg_notify($atype, $ids);
	} elseif (current_action("do_UnNotify")) {
		list($ret, $output) = pkg_notify($atype, $ids, False);
	} elseif (current_action("do_DeleteComment")) {
		list($ret, $output) = pkg_delete_comment($atype);
	} elseif (current_action("do_ChangeCategory")) {
		list($ret, $output) = pkg_change_category($pkgid, $atype);
	}

	if (isset($_REQUEST['comment'])) {
		$uid = uid_from_sid($_COOKIE["AURSID"]);
		add_package_comment($pkgid, $uid, $_REQUEST['comment']);
		$ret = true;
	}

	if ($ret) {
		/* Redirect back to package page on success. */
		header('Location: ' . get_pkg_uri($pkgname));
		exit();
	}
}

# Get package details after package actions have been attempted, FS#34508
$details = array();
if (isset($pkgname)) {
	$details = get_package_details($pkgid);
}

html_header($title, $details);
?>

<?php if ($output): ?>
	<p class="pkgoutput"><?= $output ?></p>
<?php endif; ?>

<?php
if (isset($pkgid)) {
	include('pkg_search_form.php');
	if ($pkgid) {
		if (isset($_COOKIE["AURSID"])) {
			display_package_details($pkgid, $details, $_COOKIE["AURSID"]);
		}
		else {
			display_package_details($pkgid, $details, null);
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

