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
		$pkgname = pkg_name_from_id($_GET['ID']);
	} else if (isset($_GET['N'])) {
		$pkgid = pkg_from_name($_GET['N']);
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

$details = array();
if (isset($pkgname)) {
	$details = pkg_get_details($pkgid);
}

html_header($title, $details);
?>

<script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/1.8.2/jquery.min.js"></script>
<script type="text/javascript">
function collapseDependsList(list) {
    list = $(list);
    // Hide everything past a given limit. Don't do anything if we don't have
    // enough items, or the link already exists.
    var limit = 20,
        linkid = list.attr('id') + 'link',
        items = list.find('li').slice(limit);
    if (items.length <= 1 || $('#' + linkid).length > 0) {
        return;
    }
    items.hide();
    list.after('<p><a id="' + linkid + '" href="#">Show More…</a></p>');

    // add link and wire it up to show the hidden items
    $('#' + linkid).click(function(event) {
        event.preventDefault();
        list.find('li').show();
        // remove the full <p/> node from the DOM
        $(this).parent().remove();
    });
}

$(document).ready(function() {
    collapseDependsList("#pkgdepslist");
    collapseDependsList("#pkgreqslist");
    collapseDependsList("#pkgsrcslist");
});
</script>

<?php
if (isset($pkgid)) {
	include('pkg_search_form.php');
	if ($pkgid) {
		if (isset($_COOKIE["AURSID"])) {
			pkg_display_details($pkgid, $details, $_COOKIE["AURSID"]);
		}
		else {
			pkg_display_details($pkgid, $details, null);
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

html_footer(AURWEB_VERSION);

