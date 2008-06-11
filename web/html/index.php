<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../lang');

# Add to handle the i18n of My Packages
include("pkgfuncs_po.inc");
include("aur.inc");

set_lang();
check_sid();

html_header( __("Home") );

# Newest packages
$q = "SELECT * FROM Packages WHERE DummyPkg != 1 ORDER BY GREATEST(SubmittedTS,ModifiedTS) DESC LIMIT 0 , 10";
$newest_packages = db_query($q, $dbh);

# AUR statistics
$q = "SELECT count(*) FROM Packages,PackageLocations WHERE Packages.LocationID = PackageLocations.ID AND PackageLocations.Location = 'unsupported'";
$result = db_query($q, $dbh);
$row = mysql_fetch_row($result);
$unsupported_count = $row[0];

$q = "SELECT count(*) FROM Packages,PackageLocations WHERE Packages.LocationID = PackageLocations.ID AND PackageLocations.Location = 'community'";
$result = db_query($q, $dbh);
$row = mysql_fetch_row($result);
$community_count = $row[0];

$q = "SELECT count(*) from Users";
$result = db_query($q, $dbh);
$row = mysql_fetch_row($result);
$user_count = $row[0];

$q = "SELECT count(*) from Users,AccountTypes WHERE Users.AccountTypeID = AccountTypes.ID AND AccountTypes.AccountType = 'Trusted User'";
$result = db_query($q, $dbh);
$row = mysql_fetch_row($result);
$tu_count = $row[0];

$targstamp = intval(strtotime("-7 days"));
$q = "SELECT count(*) from Packages WHERE (Packages.SubmittedTS >= $targstamp OR Packages.ModifiedTS >= $targstamp)";
$result = db_query($q, $dbh);
$row = mysql_fetch_row($result);
$update_count = $row[0];

$user = username_from_sid($_COOKIE["AURSID"]);

if (!empty($user)) {
    $q = "SELECT count(*) FROM Packages,PackageLocations,Users WHERE Packages.MaintainerUID = Users.ID AND Packages.LocationID = PackageLocations.ID AND PackageLocations.Location = 'unsupported' AND Users.Username='".mysql_real_escape_string($user)."'";
    $result = db_query($q, $dbh);
    $row = mysql_fetch_row($result);
    $maintainer_unsupported_count = $row[0];
    
    $q = "SELECT count(*) FROM Packages,Users WHERE Packages.OutOfDate = 1 AND Packages.MaintainerUID = Users.ID AND Users.Username='".mysql_real_escape_string($user)."'";
    $result = db_query($q, $dbh);
    $row = mysql_fetch_row($result);
    $flagged_outdated = $row[0];
    
    # If the user is a TU calculate the number of the packages
    $atype = account_from_sid($_COOKIE["AURSID"]);
    
    if ($atype == 'Trusted User') {    
        $q = "SELECT count(*) FROM Packages,PackageLocations,Users WHERE Packages.MaintainerUID = Users.ID AND Packages.LocationID = PackageLocations.ID AND PackageLocations.Location = 'community' AND Users.Username='".mysql_real_escape_string($user)."'";
        $result = db_query($q, $dbh);
        $row = mysql_fetch_row($result);
        $maintainer_community_count = $row[0];
    }
}

?>

<div class="pgbox">
<div class="pgboxtitle">
<span class="f3">AUR <?php print __("Home"); ?></span>
</div>
<div class="frontpgboxbody">
<table border='0' cellpadding='0' cellspacing='3' width='90%'>
<tr>
<td class='boxSoft' valign='top' colspan='2'>
<p>

<?php 
print __( 'Welcome to the AUR! Please read the %hAUR User Guidelines%h and %hAUR TU Guidelines%h for more information.'
        , '<a href="http://wiki.archlinux.org/index.php/AUR_User_Guidelines">'
        , '</a>'
        , '<a href="http://wiki.archlinux.org/index.php/AUR_Trusted_User_Guidelines">'
        , '</a>'
        );
?>

<br>

<?php
print __( 'Contributed PKGBUILDs <b>must</b> conform to the %hArch Packaging Standards%h otherwise they will be deleted!'
        , '<a href="http://wiki.archlinux.org/index.php/Arch_Packaging_Standards">'
        , '</a>'
        );
?>

</p>
<p>
<?php print __("Remember to vote for your favourite packages!"); ?>
<br>
<?php print __("The most popular packages will be provided as binary packages in [community]."); ?>
</p>
</td>
</tr>
<tr>
<td class='boxSoft' valign='top'>
<table class="boxSoft">
<tr>
<th colspan="2" class="boxSoftTitle" style="text-align: right">
<a href="/rss2.php"><img src="/images/rss.gif"></a> <span class="f3"><?php print __("Recent Updates") ?><span class="f5"></span></span>
</th>
</tr>

<?php while ($row = mysql_fetch_assoc($newest_packages)): ?>

<tr>
<td class="boxSoft">
<span class="f4"><span class="blue"><a href="/packages.php?ID=<?php print intval($row["ID"]); ?>">
<?php print $row["Name"] . ' ' . $row["Version"]; ?>
</a></span>
</td>
<td class="boxSoft">

<?php
$mod_int = intval($row["ModifiedTS"]);
$sub_int = intval($row["SubmittedTS"]);

if ($mod_int != 0):
  $modstring = gmdate("r", $mod_int);
elseif ($sub_int != 0):
  $modstring = '<img src="/images/new.gif"/> ' . gmdate("r", $sub_int);
else:
  $modstring = '(unknown)';
endif;
?>

<span class="f4"><?php print $modstring; ?></span>
</td>
</tr>

<?php endwhile; ?>

</td>
</tr>
</table>
<td class='boxSoft' valign='top'>

<?php if (!empty($user)): ?>

<table class='boxSoft'>
<tr>
<th colspan='2' class='boxSoftTitle'>
<span class='f3'><?php print __("My Statistics"); ?></span>
</th>
</tr>
<tr>
<td class='boxSoft'>
<span class='f4'><?php print __("Packages in unsupported"); ?></span>
</td>
<td class='boxSoft'>
<span class='f4'><?php print $maintainer_unsupported_count; ?></span>
</td>
</tr>

<?php if ($atype == 'Trusted User'): ?>

<tr>
<td class='boxSoft'>
<span class='f4'><?php print __("Packages in [community]"); ?></span>
</td>
<td class='boxSoft'>
<span class='f4'><?php print $maintainer_community_count; ?></span>
</td>
</tr>

<?php endif; ?>

<tr>
<td class='boxSoft'>
<span class='f4'><?php print __("Out-of-date"); ?></span>
</td>
<td class='boxSoft'>
<span class='f4'><?php print $flagged_outdated ?></span>
</td>
</tr>
</table>
<br />

<?php endif; ?>

<table class='boxSoft'>
<tr>
<th colspan='2' class='boxSoftTitle'>
<span class='f3'><?php print __("Statistics") ?></span>
</th>
</tr>
<tr>
<td class='boxSoft'>
<span class='f4'><?php print __("Packages in unsupported"); ?></span>
</td>
<td class='boxSoft'><span class='f4'><?php print $unsupported_count; ?></span></td>
</tr>
<tr>
<td class='boxSoft'>
<span class='f4'><?php print __("Packages in [community]"); ?></span>
</td>
<td class='boxSoft'><span class='f4'><?php print $community_count; ?></span></td>
</tr>
<tr>
<td class='boxSoft'>
<span class='f4'><?php print __("Packages added or updated in the past 7 days"); ?></span>
</td>
<td class='boxSoft'><span class='f4'><?php print $update_count; ?></span></td>
</tr>
<tr>
<td class='boxSoft'>
<span class='blue'><span class='f4'><?php print __("Registered Users"); ?></span></span>
</td>
<td class='boxSoft'><span class='f4'><?php print $user_count; ?></span></td>
</tr>
<tr>
<td class='boxSoft'>
<span class='f4'><?php print __("Trusted Users"); ?></span>
</td>
<td class='boxSoft'><span class='f4'><?php print $tu_count; ?></span></td>
</tr>
</table>
</td>
</tr>
</table>
<br /><span class='important'><?php print __("DISCLAIMER"); ?></span>
</div>
</div>

<?php
html_footer(AUR_VERSION);
# vim: ts=2 sw=2 noet ft=php
?>
