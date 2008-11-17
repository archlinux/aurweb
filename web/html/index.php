<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../lang');

# Add to handle the i18n of My Packages
include("pkgfuncs_po.inc");
include("aur.inc");
include('stats.inc');

set_lang();
check_sid();

html_header( __("Home") );

$dbh = db_connect();

?>

<div class="pgbox">
<div class="pgboxtitle">
<span class="f3">AUR <?php print __("Home"); ?></span>
</div>
<div class="frontpgboxbody">
<p>

<?php 
echo __(
	'Welcome to the AUR! Please read the %hAUR User Guidelines%h and %hAUR TU Guidelines%h for more information.',
	'<a href="http://wiki.archlinux.org/index.php/AUR_User_Guidelines">',
	'</a>',
	'<a href="http://wiki.archlinux.org/index.php/AUR_Trusted_User_Guidelines">',
	'</a>'
        );
?>

<br />

<?php
echo __(
	'Contributed PKGBUILDs %hmust%h conform to the %hArch Packaging Standards%h otherwise they will be deleted!',
	'<b>', '</b>',
	'<a href="http://wiki.archlinux.org/index.php/Arch_Packaging_Standards">',
	'</a>'
        );
?>

</p>
<p>
<?php echo __('Remember to vote for your favourite packages!'); ?>
<br />
<?php echo __('Some packages may be provided as binaries in [community].'); ?>
</p>
<table border='0' cellpadding='0' cellspacing='3' width='90%'>
<tr>
<td class='boxSoft' valign='top'>
<?php updates_table($dbh); ?>
</td>
<td class='boxSoft' valign='top'>
<?php
if (!empty($_COOKIE["AURSID"])) {
	$user = username_from_sid($_COOKIE["AURSID"]);
	user_table($user, $dbh);
	echo '<br />';
}

general_stats_table($dbh);
?>

</td>
</tr>
</table>

<br />
<div class="important"><?php
echo __('DISCLAIMER') . ':<br />';
echo __('Unsupported PKGBUILDs are user produced content. Any use of files is at your own risk.');
?></div>

</div>
</div>

<?php
html_footer(AUR_VERSION);

