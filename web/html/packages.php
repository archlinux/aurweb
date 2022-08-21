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

<script type="text/javascript">
function collapseDependsList(list) {
	list = document.getElementById(list);
	// Packages overview page also triggers collapseDependsList, ideally the Javascript
	// is only included for the package details view.
	if (!list) {
		return;
	}

	// Hide everything past a given limit. Don't do anything if we don't have
	// enough items, or the link already exists.
	const limit = 20;
	const linkid = list.getAttribute('id') + 'link';
	const items = Array.from(list.querySelectorAll('li')).slice(limit);
	if (items.length <= 1 || document.getElementById(linkid)) {
		return;
	}

	items.forEach(function(item) {
		item.style.display = 'none';
	});

	const link = document.createElement('a');
	link.id = linkid;
	link.href = '#';
	link.textContent = 'Show More…';

	const showMore = document.createElement('p');
	showMore.appendChild(link);

	list.insertAdjacentElement('afterend', showMore);

	// add link and wire it up to show the hidden items
	link.addEventListener('click', function(event) {
		event.preventDefault();

		items.forEach(function(item) {
			item.style.display = '';
		});

		// remove the full <p/> node from the DOM
		event.target.parentNode.removeChild(event.target);
	});
}

function collapseComment(div) {
	const linkid = div.getAttribute('id') + 'link';
	const inner = div.querySelector('div');
	// max height of a collapsed comment.
	const maxheight = 200;
	const height = inner.offsetHeight;

	if (height <= maxheight)
		return;

	inner.style.height = maxheight + 'px';
	inner.classList.add('collapsed');

	const link = document.createElement('a');
	link.id = linkid;
	link.href = '#';
	link.textContent = 'Show More…';

	const showMore = document.createElement('p');
	showMore.appendChild(link);

	inner.insertAdjacentElement('afterend', showMore);

	link.addEventListener('click', function(event) {
		const showMoreLink = event.target;
		const inner = showMoreLink.parentNode.parentNode.querySelector('div');
		var newheight;

		if (inner.classList.contains('collapsed')) {
			inner.style.height = height + 'px';
			showMoreLink.textContent = 'Collapse';
		} else {
			newheight = maxheight + 'px';
			inner.style.height = newheight;
			showMoreLink.textContent = 'Show More…';
		}

		inner.classList.toggle('collapsed');
		event.preventDefault();
	});
}

document.addEventListener('DOMContentLoaded', function() {
	collapseDependsList("pkgdepslist");
	collapseDependsList("pkgreqslist");
	collapseDependsList("pkgsrcslist");

	Array.from(document.querySelectorAll('.article-content')).forEach(collapseComment);
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
