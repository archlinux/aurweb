<?php

$pkgbuild_uri = sprintf(config_get('options', 'pkgbuild_uri'), urlencode($row['Name']));
$log_uri = sprintf(config_get('options', 'log_uri'), urlencode($row['Name']));
$snapshot_uri = sprintf(config_get('options', 'snapshot_uri'), urlencode($row['Name']));
$git_clone_uri_anon = sprintf(config_get('options', 'git_clone_uri_anon'), htmlspecialchars($row['Name']));
$git_clone_uri_priv = sprintf(config_get('options', 'git_clone_uri_priv'), htmlspecialchars($row['Name']));

$uid = uid_from_sid($SID);

$base_id = intval($row['ID']);

$keywords = pkgbase_get_keywords($base_id);

$submitter = username_from_id($row["SubmitterUID"]);
$maintainer = username_from_id($row["MaintainerUID"]);
$comaintainers = pkgbase_get_comaintainers($base_id);
$packager = username_from_id($row["PackagerUID"]);

if ($row["MaintainerUID"] !== NULL) {
	$maintainers = array_merge(array($row["MaintainerUID"]), pkgbase_get_comaintainer_uids(array($base_id)));
} else {
	$maintainers = array();
}
$unflaggers = array_merge($maintainers, array($row["FlaggerUID"]));

$votes = $row['NumVotes'];
$popularity = $row['Popularity'];

# In case of wanting to put a custom message
$msg = __('unknown');

# Print the timestamps for last updates
$updated_time = ($row["ModifiedTS"] == 0) ? $msg : date("Y-m-d H:i", intval($row["ModifiedTS"]));
$submitted_time = ($row["SubmittedTS"] == 0) ? $msg : date("Y-m-d H:i", intval($row["SubmittedTS"]));
$out_of_date_time = ($row["OutOfDateTS"] == 0) ? $msg : date("Y-m-d", intval($row["OutOfDateTS"]));

$pkgs = pkgbase_get_pkgnames($base_id);

$base_uri = get_pkgbase_uri($row['Name']);

?>
<div id="pkgdetails" class="box">
	<h2><?= __('Package Base Details') . ': ' . htmlspecialchars($row['Name']) ?></h2>

	<?php include('pkgbase_actions.php') ?>

	<table id="pkginfo">
		<tr>
			<th><?= __('Git Clone URL') . ': ' ?></th>
			<td>
				<a href="<?= $git_clone_uri_anon ?>"><?= $git_clone_uri_anon ?></a> (<?= __('read-only') ?>)
				<?php if ($uid == $row["MaintainerUID"]): ?>
				<br /> <a href="<?= $git_clone_uri_priv ?>"><?= $git_clone_uri_priv ?></a>
				<?php endif; ?>
			</td>
		</tr>
<?php
if (has_credential(CRED_PKGBASE_SET_KEYWORDS, array($row["MaintainerUID"])) || count($keywords) > 0):
?>
		<tr>
			<th><?= __('Keywords') . ': ' ?></th>
			<td>
<?php
if (has_credential(CRED_PKGBASE_SET_KEYWORDS, array($row["MaintainerUID"]))):
?>
				<form method="post" action="<?= htmlspecialchars(get_pkgbase_uri($row['Name']), ENT_QUOTES); ?>">
					<div>
						<input type="hidden" name="action" value="do_SetKeywords" />
						<?php if ($SID): ?>
						<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
						<?php endif; ?>
						<input type="text" name="keywords" value="<?= htmlspecialchars(implode(" ", $keywords), ENT_QUOTES) ?>"/>
						<input type="submit" value="<?= __('Update') ?>"/>
					</div>
				</form>
<?php
else:
	foreach ($keywords as $kw) {
		echo '<a class="keyword" href="';
		echo get_uri('/packages/') . '?K=' . urlencode($kw) . '&amp;SB=p';
		echo '">' . htmlspecialchars($kw) . "</a>\n";
	}
endif;
?>
			</td>
		</tr>
<?php endif; ?>
		<tr>
			<th><?= __('Submitter') .': ' ?></th>
			<td><?= html_format_username($submitter) ?></td>
		</tr>
		<tr>
			<th><?= __('Maintainer') .': ' ?></th>
			<td><?= html_format_maintainers($maintainer, $comaintainers) ?></td>
		</tr>
		<tr>
			<th><?= __('Last Packager') .': ' ?></th>
			<td><?= html_format_username($packager) ?></td>
		</tr>
		<tr>
			<th><?= __('Votes') . ': ' ?></th>
			<?php if (has_credential(CRED_PKGBASE_LIST_VOTERS)): ?>
			<td><a href="<?= get_pkgbase_uri($row['Name']); ?>voters/"><?= $votes ?></a></td>
			<?php else: ?>
			<td><?= $votes ?></td>
			<?php endif; ?>
		</tr>
		<tr>
			<th><?= __('Popularity') . ': ' ?></th>
			<td><?= number_format($popularity, 6) ?></td>
		</tr>
		<tr>
			<th><?= __('First Submitted') . ': ' ?></th>
			<td><?= $submitted_time ?></td>
		</tr>
		<tr>
			<th><?= __('Last Updated') . ': ' ?></th>
			<td><?= $updated_time ?></td>
		</tr>
	</table>

	<div id="metadata">
		<div id="pkgs" class="listing">
			<h3><?= __('Packages') . " (" . count($pkgs) . ")"?></h3>
<?php if (count($pkgs) > 0): ?>
			<ul>
<?php
	while (list($k, $pkg) = each($pkgs)):
?>
	<li><a href="<?= htmlspecialchars(get_pkg_uri($pkg), ENT_QUOTES); ?>" title="<?= __('View packages details for').' '. htmlspecialchars($pkg) ?>"><?= htmlspecialchars($pkg) ?></a></li>
	<?php endwhile; ?>
			</ul>
<?php endif; ?>
		</div>
	</div>
</div>
