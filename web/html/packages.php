<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc");      # access AUR common functions
set_lang();                   # this sets up the visitor's language
include_once('pkgfuncs.inc'); # package specific functions
check_sid();                  # see if they're still logged in

# Set the title to the current query if required
if (isset($_GET['ID']) && ($pkgname = pkgname_from_id($_GET['ID']))) {
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
if (current_action("do_Flag")) {
	$output = pkg_flag($atype, $ids, True);
} elseif (current_action("do_UnFlag")) {
	$output = pkg_flag($atype, $ids, False);
} elseif (current_action("do_Adopt")) {
	$output = pkg_adopt($atype, $ids, True);
} elseif (current_action("do_Disown")) {
	$output = pkg_adopt($atype, $ids, False);
} elseif (current_action("do_Vote")) {
	$output = pkg_vote($atype, $ids, True);
} elseif (current_action("do_UnVote")) {
	$output = pkg_vote($atype, $ids, False);
} elseif (current_action("do_Delete")) {
	if (isset($_POST['confirm_Delete'])) {
		$output = pkg_delete($atype, $ids);
		unset($_GET['ID']);
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

html_header($title);
?>

<?php if ($output): ?>
	<p class="pkgoutput"><?php print $output ?></p>
<?php endif; ?>

<?php
if (isset($_GET['ID'])) {
	include('pkg_search_form.php');
	if (!$_GET['ID'] = intval($_GET['ID'])) {
		print __("Error trying to retrieve package details.")."<br />\n";
	} else {
		if (isset($_COOKIE["AURSID"])) {
			package_details($_GET['ID'], $_COOKIE["AURSID"]);
		}
		else {
			package_details($_GET['ID'], null);
		}
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

