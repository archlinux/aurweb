<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
set_lang();
include_once('pkgfuncs.inc.php');
check_sid();

/*
 * Retrieve package base ID and name, unless initialized by the routing
 * framework.
 */
if (!isset($base_id) || !isset($pkgbase_name)) {
	if (isset($_GET['ID'])) {
		$base_id = intval($_GET['ID']);
		$pkgbase_name = pkgbase_name_from_id($_GET['ID']);
	} else if (isset($_GET['N'])) {
		$base_id = pkgbase_from_name($_GET['N']);
		$pkgbase_name = $_GET['N'];
	} else {
		unset($base_id, $pkgbase_name);
	}

	if (isset($base_id) && ($base_id == 0 || $base_id == NULL || $pkgbase_name == NULL)) {
		header("HTTP/1.0 404 Not Found");
		include "./404.php";
		return;
	}
}

/* Set the title to package base name. */
$title = $pkgbase_name;

/* Retrieve account type. */
if (isset($_COOKIE["AURSID"])) {
	$atype = account_from_sid($_COOKIE["AURSID"]);
} else {
	$atype = "";
}

/* Grab the list of package base IDs to be operated on. */
$ids = array();
if (isset($_POST['IDs'])) {
	foreach ($_POST['IDs'] as $id => $i) {
		$id = intval($id);
		if ($id > 0) {
			$ids[] = $id;
		}
	}
}

/* Perform package base actions. */
$ret = false;
$output = "";
if (check_token()) {
	if (current_action("do_Flag")) {
		list($ret, $output) = pkgbase_flag($atype, $ids);
	} elseif (current_action("do_UnFlag")) {
		list($ret, $output) = pkgbase_unflag($atype, $ids);
	} elseif (current_action("do_Adopt")) {
		list($ret, $output) = pkgbase_adopt($atype, $ids, true, NULL);
	} elseif (current_action("do_Disown")) {
		$via = isset($_POST['via']) ? $_POST['via'] : NULL;
		list($ret, $output) = pkgbase_adopt($atype, $ids, false, $via);
	} elseif (current_action("do_Vote")) {
		list($ret, $output) = pkgbase_vote($atype, $ids, true);
	} elseif (current_action("do_UnVote")) {
		list($ret, $output) = pkgbase_vote($atype, $ids, false);
	} elseif (current_action("do_Delete")) {
		if (isset($_POST['confirm_Delete'])) {
			$via = isset($_POST['via']) ? $_POST['via'] : NULL;
			if (!isset($_POST['merge_Into']) || empty($_POST['merge_Into'])) {
				list($ret, $output) = pkgbase_delete($atype, $ids, NULL, $via);
				unset($_GET['ID']);
			}
			else {
				$merge_base_id = pkgbase_from_name($_POST['merge_Into']);
				if ($merge_base_id) {
					list($ret, $output) = pkgbase_delete($atype, $ids, $merge_base_id, $via);
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
		list($ret, $output) = pkgbase_notify($atype, $ids);
	} elseif (current_action("do_UnNotify")) {
		list($ret, $output) = pkgbase_notify($atype, $ids, false);
	} elseif (current_action("do_DeleteComment")) {
		list($ret, $output) = pkgbase_delete_comment($atype);
	} elseif (current_action("do_ChangeCategory")) {
		list($ret, $output) = pkgbase_change_category($base_id, $atype);
	} elseif (current_action("do_FileRequest")) {
		list($ret, $output) = pkgbase_file_request($ids, $_POST['type'], $_POST['merge_into'], $_POST['comments']);
	} elseif (current_action("do_CloseRequest")) {
		list($ret, $output) = pkgbase_close_request($_POST['reqid']);
	}

	if (isset($_REQUEST['comment'])) {
		$uid = uid_from_sid($_COOKIE["AURSID"]);
		pkgbase_add_comment($base_id, $uid, $_REQUEST['comment']);
		$ret = true;
	}

	if ($ret) {
		if (current_action("do_CloseRequest")) {
			/* Redirect back to package request page on success. */
			header('Location: ' . get_pkgreq_route());
			exit();
		} if (isset($base_id)) {
			/* Redirect back to package base page on success. */
			header('Location: ' . get_pkgbase_uri($pkgbase_name));
			exit();
		} else {
			/* Redirect back to package search page. */
			header('Location: ' . get_pkg_route());
			exit();
		}
	}
}

$pkgs = pkgbase_get_pkgnames($base_id);
if (count($pkgs) == 1) {
	/* Not a split package. Redirect to the package page. */
	if (empty($_SERVER['QUERY_STRING'])) {
		header('Location: ' . get_pkg_uri($pkgs[0]));
	} else {
		header('Location: ' . get_pkg_uri($pkgs[0]) . '?' . $_SERVER['QUERY_STRING']);
	}
}

$details = pkgbase_get_details($base_id);
html_header($title, $details);
?>

<?php if ($output): ?>
<p class="pkgoutput"><?= $output ?></p>
<?php endif; ?>

<?php
include('pkg_search_form.php');
if (isset($_COOKIE["AURSID"])) {
	pkgbase_display_details($base_id, $details, $_COOKIE["AURSID"]);
} else {
	pkgbase_display_details($base_id, $details, null);
}

html_footer(AUR_VERSION);

