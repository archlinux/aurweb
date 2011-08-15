<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
set_lang();
check_sid();

include_once('stats.inc.php');

html_header( __("Home") );

include('pkg_search_form.php');

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
	'Welcome to the AUR! Please read the %sAUR User Guidelines%s and %sAUR TU Guidelines%s for more information.',
	'<a href="http://wiki.archlinux.org/index.php/AUR_User_Guidelines">',
	'</a>',
	'<a href="http://wiki.archlinux.org/index.php/AUR_Trusted_User_Guidelines">',
	'</a>'
        );
?>

<br />

<?php
echo __(
	'Contributed PKGBUILDs %smust%s conform to the %sArch Packaging Standards%s otherwise they will be deleted!',
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
echo __('Unsupported packages are user produced content. Any use of the provided files is at your own risk.');
?></div>

</div>
</div>

<?php
html_footer(AUR_VERSION);

