<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../lang');

include("aur.inc");         # access AUR common functions
include("pkgfuncs.inc");    # package specific functions
include("search_po.inc");   # use some form of this for i18n support
set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in

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

html_header($title);

# Determine what action to do
if ($_POST['action'] == "do_Flag" || isset($_POST['do_Flag'])) {
	print "<p>";
	print pkg_flag($atype, $ids, True);
	print "</p>";
} elseif ($_POST['action'] == "do_UnFlag" || isset($_POST['do_UnFlag'])) {
	print "<p>";
	print pkg_flag($atype, $ids, False);
	print "</p>";
} elseif ($_POST['action'] == "do_Adopt" || isset($_POST['do_Adopt'])) {
	print "<p>";
	print pkg_adopt($atype, $ids, True);
	print "</p>";
} elseif ($_POST['action'] == "do_Disown" || isset($_POST['do_Disown'])) {
	print "<p>";
	print pkg_adopt($atype, $ids, False);
	print "</p>";
} elseif ($_POST['action'] == "do_Vote" || isset($_POST['do_Vote'])) {
	print "<p>";
	print pkg_vote($atype, $ids, True);
	print "</p>";
} elseif ($_POST['action'] == "do_UnVote" || isset($_POST['do_UnVote'])) {
	print "<p>";
	print pkg_vote($atype, $ids, False);
	print "</p>";
} elseif ($_POST['action'] == "do_Delete" || isset($_POST['do_Delete'])) {
	print "<p>";
	print pkg_delete($atype, $ids);
	print "</p>";
} elseif ($_POST['action'] == "do_Notify" || isset($_POST['do_Notify'])) {
	print "<p>";
	print pkg_notify($atype, $ids);
	print "</p>";
} elseif ($_POST['action'] == "do_UnNotify" || isset($_POST['do_UnNotify'])) {
	print "<p>";
	print pkg_notify($atype, $ids, False);
	print "</p>";
} elseif (isset($_GET["ID"])) {

	if (!intval($_GET["ID"])) {
		print __("Error trying to retrieve package details.")."<br />\n";
		
	} else {
		package_details($_GET["ID"], $_COOKIE["AURSID"]);
	}

} else {
	pkg_search_page($_COOKIE["AURSID"]);
}

html_footer(AUR_VERSION);

