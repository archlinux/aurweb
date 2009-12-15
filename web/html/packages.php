<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc");      # access AUR common functions
set_lang();                   # this sets up the visitor's language
include_once('pkgfuncs.inc'); # package specific functions
check_sid();                  # see if they're still logged in

# Set the title to the current query if required
if (isset($_GET['ID'])) {
	if ($pkgname = pkgname_from_id($_GET['ID'])) { $title = $pkgname; }
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
		$ids[] = $id;
	}
}

# Determine what action to do
$output = "";
if ($_POST['action'] == "do_Flag" || isset($_POST['do_Flag'])) {
	$output = pkg_flag($atype, $ids, True);
} elseif ($_POST['action'] == "do_UnFlag" || isset($_POST['do_UnFlag'])) {
	$output = pkg_flag($atype, $ids, False);
} elseif ($_POST['action'] == "do_Adopt" || isset($_POST['do_Adopt'])) {
	$output = pkg_adopt($atype, $ids, True);
} elseif ($_POST['action'] == "do_Disown" || isset($_POST['do_Disown'])) {
	$output = pkg_adopt($atype, $ids, False);
} elseif ($_POST['action'] == "do_Vote" || isset($_POST['do_Vote'])) {
	$output = pkg_vote($atype, $ids, True);
} elseif ($_POST['action'] == "do_UnVote" || isset($_POST['do_UnVote'])) {
	$output = pkg_vote($atype, $ids, False);
} elseif ($_POST['action'] == "do_Delete" || isset($_POST['do_Delete'])) {
	$output = pkg_delete($atype, $ids);
	unset($_GET['ID']);
} elseif ($_POST['action'] == "do_Notify" || isset($_POST['do_Notify'])) {
	$output = pkg_notify($atype, $ids);
} elseif ($_POST['action'] == "do_UnNotify" || isset($_POST['do_UnNotify'])) {
	$output = pkg_notify($atype, $ids, False);
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
		package_details($_GET['ID'], $_COOKIE["AURSID"]);
	}
} else {
	$_GET['SB'] = 'v';
	$_GET['SO'] = 'd';
	pkg_search_page($_COOKIE["AURSID"]);
}

html_footer(AUR_VERSION);

