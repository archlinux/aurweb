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
	<link rel='alternate' type='application/rss+xml' title='Newest Packages RSS' href='rss2.php' />
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  </head>
  <body>
    <div id="head_container">
      <div id="title">
        <div id="logo"><h1 id="archtitle"><a href="http://www.archlinux.org/" title="Arch Linux (Home)">Arch Linux</a></h1></div>
      </div>
      <div id="main_nav">
        <ul>
          <li><a href="http://www.archlinux.org/download/">Download</a></li>
          <li class="selected"><a href="index.php">AUR</a></li>
          <li><a href="http://bugs.archlinux.org/">Bugs</a></li>
          <li><a href="http://wiki.archlinux.org/">Wiki</a></li>
          <li><a href="http://bbs.archlinux.org/">Forums</a></li>
          <li><a href="http://www.archlinux.org/">Home</a></li>
        </ul>
      </div>
        <div id="ads">
            <script type="text/javascript"><!--
                google_ad_client = "pub-3170555743375154";
                google_ad_width = 468;
                google_ad_height = 60;
                google_ad_format = "468x60_as";
                google_color_border = "ffffff";
                google_color_bg = "ffffff";
                google_color_link = "0771A6";
                google_color_url = "99AACC";
                google_color_text = "000000";
            //--></script>
            <script type="text/javascript" src="http://pagead2.googlesyndication.com/pagead/show_ads.js"></script>
        </div>
      <div id="sub_nav">
        <ul>
<?php
if (isset($_COOKIE["AURSID"])) {
?>
	      <li><a href="pkgsubmit.php"><?php print __("Submit"); ?></a></li>
          <li><a href="packages.php?SeB=m&K=<?php print username_from_sid($_COOKIE["AURSID"]); ?>"><?php print __("My Packages"); ?></a></li>
<?php
	$SID = $_COOKIE['AURSID'];
	$atype = account_from_sid($SID);
	if ($atype == "Trusted User" || $atype == "Developer") {
?>
	      <li><a href="tu.php"><?php print __("Trusted User"); ?></a></li>
<?php
	}
}
?>
          <li><a href="http://archlinux.org/mailman/listinfo/aur-general">
	<?php print __("Discussion"); ?></a></li>
	      <li><a href="http://bugs.archlinux.org/index.php?tasks=all&amp;project=2"><?php print __("Bugs"); ?></a></li>
          <li><a href="packages.php"><?php print __("Packages"); ?></a></li>
          <li><a href="account.php"><?php print __("Accounts"); ?></a></li>
          <li><a href="index.php">AUR <?php print __("Home"); ?></a></li>
        </ul>
      </div>
    </div>
    <div id="lang_login_sub">
        <ul>
          <li>Lang: </li>
<?php
reset($SUPPORTED_LANGS);
foreach ($SUPPORTED_LANGS as $lang => $lang_name) {
        print '<li><a href="'
                . $_SERVER["PHP_SELF"]."?setlang=$lang\""
		. " title=\"" . $SUPPORTED_LANGS[$lang]. "\">"
		. strtoupper($lang) . "</a></li>\n";
}
?>
        </ul>
	<?php include("login_form.php"); ?>
    </div>
    <div id="maincontent">
	  <!-- Start of main content -->


