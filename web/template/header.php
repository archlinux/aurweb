<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"
	xml:lang="<?php print "$LANG\" lang=\"$LANG"; ?>">
  <head>
    <title>AUR (<?php print $LANG; ?>)<?php if ($title != "") { print " - " . $title; } ?></title>
	<link rel='stylesheet' type='text/css' href='css/fonts.css' />
	<link rel='stylesheet' type='text/css' href='css/containers.css' />
	<link rel='stylesheet' type='text/css' href='css/arch.css' />
	<link rel='stylesheet' type='text/css' href='css/archnavbar/archnavbar.css' />
	<link rel='shortcut icon' href='images/favicon.ico' />
	<link rel='alternate' type='application/rss+xml' title='Newest Packages RSS' href='rss.php' />
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  </head>
	<body>
		<div id="archnavbar" class="anb-aur">
			<div id="archnavbarlogo"><h1><a href="/" title="Return to the main page">Arch Linux</a></h1></div>
			<div id="archnavbarmenu">
				<ul id="archnavbarlist">
					<li id="anb-home"><a href="http://archlinux.org/" title="Arch news, packages, projects and more">Home</a></li>
					<li id="anb-packages"><a href="http://archlinux.org/packages/" title="Arch Package Database">Packages</a></li>
					<li id="anb-forums"><a href="http://bbs.archlinux.org/" title="Community forums">Forums</a></li>
					<li id="anb-wiki"><a href="http://wiki.archlinux.org/" title="Community documentation">Wiki</a></li>
					<li id="anb-bugs"><a href="http://bugs.archlinux.org/" title="Report and track bugs">Bugs</a></li>
					<li id="anb-aur"><a href="http://aur.archlinux.org/" title="Arch Linux User Repository">AUR</a></li>
					<li id="anb-download"><a href="http://archlinux.org/download/" title="Get Arch Linux">Download</a></li>
				</ul>
			</div>
		</div><!-- #archnavbar -->

		<div id="archdev-navbar">
			<ul>
				<li><a href="index.php">AUR <?php print __("Home"); ?></a></li>
				<li><a href="account.php"><?php print __("Accounts"); ?></a></li>
				<li><a href="packages.php"><?php print __("Packages"); ?></a>
				<li><a href="http://bugs.archlinux.org/index.php?tasks=all&amp;project=2"><?php print __("Bugs"); ?></a></li>
				<li><a href="http://archlinux.org/mailman/listinfo/aur-general"><?php print __("Discussion"); ?></a></li>
				<?php if (isset($_COOKIE['AURSID'])): ?>
					<?php if (check_user_privileges()): ?><li><a href="tu.php"><?php print __("Trusted User"); ?></a><?php endif; ?>
					<li><a href="packages.php?SeB=m&K=<?php print username_from_sid($_COOKIE["AURSID"]); ?>"><?php print __("My Packages"); ?></a></li>
					<li><a href="pkgsubmit.php"><?php print __("Submit"); ?></a></li>
				<?php endif; ?>
			</ul>
		</div><!-- #archdev-navbar -->

		<?php include("login_form.php"); ?>

	<div id="lang_sub">
<?php
reset($SUPPORTED_LANGS);
foreach ($SUPPORTED_LANGS as $lang => $lang_name) {
        print '<a href="'
                . $_SERVER["PHP_SELF"]."?setlang=$lang\""
		. " title=\"$lang_name\">"
		. strtolower($lang) . "</a>\n";
}
?>
	</div>
	<!-- Start of main content -->


