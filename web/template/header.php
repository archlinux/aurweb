<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"
	xml:lang="<?php print "$LANG\" lang=\"$LANG"; ?>">
  <head>
    <title>AUR (<?php print $LANG; ?>)<?php if ($title != "") { print " - " . $title; } ?></title>
	<link rel='stylesheet' type='text/css' href='/css/fonts.css' />
	<link rel='stylesheet' type='text/css' href='/css/containers.css' />
	<link rel='stylesheet' type='text/css' href='/css/arch.css' />
	<link rel='shortcut icon' href='images/favicon.ico' />
	<link rel='alternate' type='application/rss+xml' title='Newest Packages RSS' href='rss2.php' />
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  </head>
  <body bgcolor='white'>
    <div id="head_container">
      <div id="title">
        <div id="logo"><h1 id="archtitle"><a href="/" title="Arch Linux (Home)">Arch Linux</a></h1></div>
      </div>
      <div id="main_nav">
        <ul>
          <li><a href="http://www.archlinux.org/download/">Get Arch</a></li>
          <li class="selected"><a href="http://aur.archlinux.org">AUR</a></li>
          <li><a href="http://bugs.archlinux.org">Bugs</a></li>
          <li><a href="http://wiki.archlinux.org">Wiki</a></li>
          <li><a href="http://bbs.archlinux.org">Forums</a></li>
          <li><a href="http://www.archlinux.org">Home</a></li>
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
	      <li><a href="/logout.php"><?php print __("Logout"); ?></a></li>
	      <li><a href="/pkgsubmit.php"><?php print __("Submit"); ?></a></li>
	      <li><a href="/packages.php?do_MyPackages=1"><?php print __("My Packages"); ?></a></li>
<?php
	if (account_from_sid($_COOKIE["AURSID"]) == "Trusted User"
		|| account_from_sid($_COOKIE["AURSID"]) == "Developer") {
?>
	      <li><a href="/tu.php"><?php print __("Trusted User"); ?></a></li>
<?php
	}
}
?>
          <li><a href="http://archlinux.org/mailman/listinfo/aur-general">
	<?php print __("Discussion"); ?></a></li>
	      <li><a href="http://bugs.archlinux.org/index.php?tasks=all&project=2"><?php print __("Bugs"); ?></a></li>
          <li><a href="packages.php"><?php print __("Packages"); ?></a></li>
          <li><a href="account.php"><?php print __("Accounts"); ?></a></li>
          <li><a href="index.php">AUR <?php print __("Home"); ?></a></li>
        </ul>
      </div>
    </div>
    <div id="lang_login_sub">
	    <span id="lang_bar">
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
        </span>
        <span id="login_bar">
<?php
if (isset($_COOKIE["AURSID"])) {
  print __("Logged-in as: %h%s%h",
			array("<b>", username_from_sid($_COOKIE["AURSID"]), "</b>"));
} else {
	if ($login_error) {
		print "<span class='error'>" . $login_error . "</span><br />\n";
    } ?>
        <form method='post'>
         <?php print __("Username:"); ?>
          <input type='text' name='user' size='30' maxlength='64' value='<?php if (isset($_POST['user'])) { print htmlspecialchars($_POST['user'], ENT_QUOTES); } ?>'>
         <?php print __("Password:"); ?>
          <input type='password' name='pass' size='30' maxlength='32'>
          <input type='submit' class='button' value='<?php  print __("Login"); ?>'>
        </form>
<?php } ?>
        </span>
      </div>
    </div>
    <div id="maincontent">
	  <!-- Start of main content -->


