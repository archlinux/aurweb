<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");      # access AUR common functions
include_once('pkgfuncs.inc.php'); # package specific functions

# Retrieve package ID and name, unless initialized by the routing framework
if (!isset($pkgid) || !isset($pkgname)) {
	if (isset($_GET['ID'])) {
		$pkgid = intval($_GET['ID']);
	} else if (isset($_GET['N'])) {
		$pkgid = pkg_from_name($_GET['N']);
	} else {
		unset($pkgid);
	}
}

$details = array();
if (isset($pkgid)) {
	$details = pkg_get_details($pkgid);
	if (isset($details['Name'])) {
		$pkgname = $details['Name'];
	} else {
		$pkgname = null;
	}
} else {
	unset($pkgname);
}

if (isset($pkgid) && ($pkgid == 0 || $pkgid == NULL || $pkgname == NULL)) {
	header("HTTP/1.0 404 Not Found");
	include "./404.php";
	return;
}

# Set the title to the current query or package name
if (isset($pkgname)) {
	$title = $pkgname;
} else if (!empty($_GET['K'])) {
	$title = __("Search Criteria") . ": " . $_GET['K'];
} else {
	$title = __("Packages");
}

html_header($title, $details);
?>

<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/jquery@1.9.1/jquery.min.js"></script>
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

function collapseComment(div) {
	var linkid = div.attr('id') + 'link',
		inner = div.find('div'),
		height = inner.height(),
		maxheight = 200;

	if (height <= maxheight)
		return;

	inner.css({ 'overflow': 'hidden', 'height': maxheight + 'px' });
	inner.addClass('collapsed');
	inner.after('<p><a id="' + linkid + '" href="#">Show More…</a></p>');

	$('#' + linkid).click(function(event) {
		var inner = $(this).parent().parent().find('div');
		var newheight;

		if (inner.hasClass('collapsed')) {
			inner.css({ 'height': 'auto' });
			newheight = inner.height();
			inner.css({ 'height': maxheight });
			$(this).text('Collapse');
		} else {
			newheight = maxheight;
			$(this).text('Show More…');
		}

		inner.animate({ 'height': newheight });
		inner.toggleClass('collapsed');
		event.preventDefault();
	});
}

$(document).ready(function() {
	collapseDependsList("#pkgdepslist");
	collapseDependsList("#pkgreqslist");
	collapseDependsList("#pkgsrcslist");
	$(".article-content").each(function() {
		collapseComment($(this));
	});
});
</script>

<?php
include('pkg_search_form.php');

if (isset($pkgid)) {
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
		$_GET['SB'] = 'p';
		$_GET['SO'] = 'd';
	}
	echo '<div id="pkglist-results" class="box">';
	if (isset($_COOKIE["AURSID"])) {
		pkg_search_page($_GET, true, $_COOKIE["AURSID"]);
	} else {
		pkg_search_page($_GET, true);
	}
	echo '</div>';
}

html_footer(AURWEB_VERSION);

