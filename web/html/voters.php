<?php
set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');
include_once('aur.inc.php');
include_once('pkgfuncs.inc.php');

$SID = $_COOKIE['AURSID'];
$pkgname = htmlspecialchars($_GET['N']);
$votes = pkgbase_votes_from_name($pkgname);

html_header(__("Voters"));

if (has_credential(CRED_PKGBASE_LIST_VOTERS)):
?>

<div class="box">
	<h2>Votes for <a href="<?= get_pkg_uri($pkgname); ?>"><?= $pkgname ?></a></h2>
	<div class="boxbody">
		<ul>
			<?php while (list($indx, $row) = each($votes)): ?>
			<li><a href="<?= get_user_uri($row['Username']); ?>"><?= htmlspecialchars($row['Username']) ?></a></li>
			<?php endwhile; ?>
		</ul>
	</div>
</div>

<?php
endif;

html_footer(AUR_VERSION);
