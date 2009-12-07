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
	<link rel='shortcut icon' href='images/favicon.ico' />
	<link rel='alternate' type='application/rss+xml' title='Newest Packages RSS' href='rss.php' />
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  </head>
  <body>
      <div id="title">
        <div id="logo"><h1 id="archtitle"><a href="http://www.archlinux.org/" title="Arch Linux (Home)">Arch Linux</a></h1></div>
      </div>
      <div id="main_nav">
          <a href="http://www.archlinux.org/">Home</a>
          <a href="http://bbs.archlinux.org/">Forums</a>
          <a href="http://wiki.archlinux.org/">Wiki</a>
          <a href="http://bugs.archlinux.org/">Bugs</a>
          <a class="selected" href="index.php">AUR</a>
          <a href="http://www.archlinux.org/download/">Download</a>
      </div>
      <div id="sub_nav">
	<a href="index.php">AUR <?php print __("Home"); ?></a>
	<a href="account.php"><?php print __("Accounts"); ?></a>
	<a href="packages.php"><?php print __("Packages"); ?></a>
	<a href="http://bugs.archlinux.org/index.php?tasks=all&amp;project=2"><?php print __("Bugs"); ?></a>
	<a href="http://archlinux.org/mailman/listinfo/aur-general">
	<?php print __("Discussion"); ?></a>
<?php
if (isset($_COOKIE["AURSID"])) {
	$SID = $_COOKIE['AURSID'];
	$atype = account_from_sid($SID);
	if ($atype == "Trusted User" || $atype == "Developer") {
?>
	<a href="tu.php"><?php print __("Trusted User"); ?></a>
<?php
	}
?>
	<a href="packages.php?SeB=m&K=<?php print username_from_sid($_COOKIE["AURSID"]); ?>"><?php print __("My Packages"); ?></a>
	<a href="pkgsubmit.php"><?php print __("Submit"); ?></a>
<?php
}
?>

      </div>
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


