<?php
set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');
include_once('aur.inc.php');
include_once('pkgfuncs.inc.php');

$SID = $_COOKIE['AURSID'];

$pkgid = intval($_GET['ID']);
$votes = getvotes($pkgid);
$atype = account_from_sid($SID);

html_header(__("Voters"));

if ($atype == 'Trusted User' || $atype== 'Developer'):
?>

<div class="box">
	<h2>Votes for <a href="<?php echo get_pkg_uri(pkgname_from_id($pkgid)); ?>"><?php echo pkgname_from_id($pkgid) ?></a></h2>
	<div class="boxbody">

<?php
	while (list($indx, $row) = each($votes)): ?>
		<a href="<?php echo get_uri('/account/'); ?>?Action=AccountInfo&amp;ID=<?php echo $row['UsersID'] ?>"><?php echo htmlspecialchars($row['Username']) ?></a><br />
	<?php endwhile; ?>
	</div>
</div>

<?php
endif;

html_footer(AUR_VERSION);
