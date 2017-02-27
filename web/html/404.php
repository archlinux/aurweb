<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

$path = $_SERVER['PATH_INFO'];
$tokens = explode('/', $path);

if (isset($tokens[1]) && preg_match('/^([a-z0-9][a-z0-9.+_-]*?)(\.git)?$/', $tokens[1], $matches)) {
	$gitpkg = $matches[1];
	if (pkg_from_name($gitpkg)) {
		$gitcmd = 'git clone ' . sprintf(config_get('options', 'git_clone_uri_anon'), htmlspecialchars($gitpkg));
		$gitlink = get_pkgbase_uri($gitpkg);
	} else {
		unset($gitpkg);
	}
} else {
	unset($gitpkg);
}

html_header( __("Page Not Found") );
?>

<div id="error-page" class="box 404">
	<h2>404 - <?= __("Page Not Found") ?></h2>
	<p><?= __("Sorry, the page you've requested does not exist.") ?></p>
	<?php if (isset($gitpkg)): ?>
	<ul>
		<li>
			<strong><?= __("Note") ?>:</strong>
			<?= __("Git clone URLs are not meant to be opened in a browser.") ?>
		</li>
		<li>
			<?= __("To clone the Git repository of %s, run %s.",
				'<strong>' . htmlspecialchars($gitpkg) . '</strong>',
				'<code>' . htmlspecialchars($gitcmd) . '</code>') ?>
		</li>
		<li>
			<?= __("Click %shere%s to return to the %s details page.",
				'<a href="' . htmlspecialchars($gitlink, ENT_QUOTES) . '">', '</a>',
				'<strong>' . htmlspecialchars($gitpkg) . '</strong>') ?>
		</li>
	</ul>
	<?php endif; ?>
</div>

<?php
html_footer(AURWEB_VERSION);
