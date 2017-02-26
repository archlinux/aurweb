<?php
set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');
include_once('aur.inc.php');
include_once('pkgbasefuncs.inc.php');

$SID = $_COOKIE['AURSID'];
$pkgbase_name = htmlspecialchars($_GET['N']);
$votes = pkgbase_votes_from_name($pkgbase_name);

html_header(__("Voters"));

if (has_credential(CRED_PKGBASE_LIST_VOTERS)):
?>

<div class="box">
	<h2>Votes for <a href="<?= get_pkgbase_uri($pkgbase_name); ?>"><?= $pkgbase_name ?></a></h2>
	<div class="boxbody">
		<ul>
			<?php while (list($indx, $row) = each($votes)): ?>
			<li>
				<a href="<?= get_user_uri($row['Username']); ?>"><?= htmlspecialchars($row['Username']) ?></a>
				<?php if ($row["VoteTS"] > 0): ?>
				(<?= date("Y-m-d H:i", intval($row["VoteTS"])) ?>)
				<?php endif; ?>
			</li>
			<?php endwhile; ?>
		</ul>
	</div>
</div>

<?php
endif;

html_footer(AURWEB_VERSION);
