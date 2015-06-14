<?php

$pkgbuild_uri = sprintf(config_get('options', 'pkgbuild_uri'), urlencode($row['BaseName']));
$log_uri = sprintf(config_get('options', 'log_uri'), urlencode($row['BaseName']));
$snapshot_uri = sprintf(config_get('options', 'snapshot_uri'), urlencode($row['BaseName']));
$git_clone_uri_anon = sprintf(config_get('options', 'git_clone_uri_anon'), htmlspecialchars($row['BaseName']));
$git_clone_uri_priv = sprintf(config_get('options', 'git_clone_uri_priv'), htmlspecialchars($row['BaseName']));

$uid = uid_from_sid($SID);

$pkgid = intval($row['ID']);
$base_id = intval($row['BaseID']);

$keywords = pkgbase_get_keywords($base_id);

$submitter = username_from_id($row["SubmitterUID"]);
$maintainer = username_from_id($row["MaintainerUID"]);
$comaintainers = pkgbase_get_comaintainers($base_id);
$packager = username_from_id($row["PackagerUID"]);

$votes = $row['NumVotes'];

# In case of wanting to put a custom message
$msg = __('unknown');
$license = empty($row['License']) ? $msg : $row['License'];

# Print the timestamps for last updates
$updated_time = ($row["ModifiedTS"] == 0) ? $msg : gmdate("Y-m-d H:i", intval($row["ModifiedTS"]));
$submitted_time = ($row["SubmittedTS"] == 0) ? $msg : gmdate("Y-m-d H:i", intval($row["SubmittedTS"]));
$out_of_date_time = ($row["OutOfDateTS"] == 0) ? $msg : gmdate("Y-m-d", intval($row["OutOfDateTS"]));

$lics = pkg_licenses($row["ID"]);
$grps = pkg_groups($row["ID"]);

$deps = pkg_dependencies($row["ID"]);
$requiredby = pkg_required($row["Name"]);

usort($deps, function($x, $y) {
	if ($x[1] != $y[1]) {
		if ($x[1] == "depends") {
			return -1;
		} elseif ($y[1] == "depends") {
			return 1;
		}
		return strcmp($x[1], $y[1]);
	} elseif ($x[3] != $y[3]) {
		return strcmp($x[3], $y[3]);
	} else {
		return strcmp($x[0], $y[0]);
	}
});

$rels = pkg_relations($row["ID"]);

usort($rels, function($x, $y) {
	if ($x[3] != $y[3]) {
		return strcmp($x[3], $y[3]);
	} else {
		return strcmp($x[0], $y[0]);
	}
});

$rels_c = $rels_p = $rels_r = array();
foreach ($rels as $rel) {
	switch ($rel[1]) {
	case "conflicts":
		$rels_c[] = $rel;
		break;
	case "provides":
		$rels_p[] = $rel;
		break;
	case "replaces":
		$rels_r[] = $rel;
		break;
	}
}

# $sources[0] = 'src';
$sources = pkg_sources($row["ID"]);
?>
<div id="pkgdetails" class="box">
	<h2><?= __('Package Details') . ': ' . htmlspecialchars($row['Name']) . ' ' . htmlspecialchars($row['Version']) ?></h2>
	<div id="detailslinks" class="listing">
		<div id="actionlist">
			<h4><?= __('Package Actions') ?></h4>
			<ul class="small">
				<li>
					<a href="<?= $pkgbuild_uri ?>"><?= __('View PKGBUILD') ?></a> /
					<a href="<?= $log_uri ?>"><?= __('View Changes') ?></a>
				</li>
				<li><a href="<?= $snapshot_uri ?>"><?= __('Download snapshot') ?></a>
				<li><a href="https://wiki.archlinux.org/index.php/Special:Search?search=<?= urlencode($row['Name']) ?>"><?= __('Search wiki') ?></a></li>
				<li><span class="flagged"><?php if ($row["OutOfDateTS"] !== NULL) { echo __('Flagged out-of-date')." (${out_of_date_time})"; } ?></span></li>
				<?php if ($uid): ?>
				<?php if ($row["OutOfDateTS"] === NULL): ?>
				<li>
					<form action="<?= get_pkgbase_uri($row['BaseName']) . 'flag/'; ?>" method="post">
						<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
						<input type="submit" class="button text-button" name="do_Flag" value="<?= __('Flag package out-of-date') ?>" />
					</form>
				</li>
				<?php elseif (($row["OutOfDateTS"] !== NULL) && has_credential(CRED_PKGBASE_UNFLAG, array($row["MaintainerUID"]))): ?>
				<li>
					<form action="<?= get_pkgbase_uri($row['BaseName']) . 'unflag/'; ?>" method="post">
						<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
						<input type="submit" class="button text-button" name="do_UnFlag" value="<?= __('Unflag package') ?>" />
					</form>
				</li>
				<?php endif; ?>
				<?php if (pkgbase_user_voted($uid, $base_id)): ?>
				<li>
					<form action="<?= get_pkgbase_uri($row['BaseName']) . 'unvote/'; ?>" method="post">
						<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
						<input type="submit" class="button text-button" name="do_UnVote" value="<?= __('Remove vote') ?>" />
					</form>
				</li>
				<?php else: ?>
				<li>
					<form action="<?= get_pkgbase_uri($row['BaseName']) . 'vote/'; ?>" method="post">
						<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
						<input type="submit" class="button text-button" name="do_Vote" value="<?= __('Vote for this package') ?>" />
					</form>
				</li>
				<?php endif; ?>
				<?php if (pkgbase_user_notify($uid, $base_id)): ?>
				<li>
					<form action="<?= get_pkgbase_uri($row['BaseName']) . 'unnotify/'; ?>" method="post">
						<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
						<input type="submit" class="button text-button" name="do_UnNotify" value="<?= __('Disable notifications') ?>" />
					</form>
				</li>
				<?php else: ?>
				<li>
					<form action="<?= get_pkgbase_uri($row['BaseName']) . 'notify/'; ?>" method="post">
						<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
						<input type="submit" class="button text-button" name="do_Notify" value="<?= __('Notify of new comments') ?>" />
					</form>
				</li>
				<?php endif; ?>
				<?php if (has_credential(CRED_PKGBASE_EDIT_COMAINTAINERS, array($row["MaintainerUID"]))): ?>
				<li><a href="<?= get_pkgbase_uri($row['BaseName']) . 'comaintainers/'; ?>"><?= __('Manage Co-Maintainers'); ?></a></li>
				<?php endif; ?>
				<li><span class="flagged"><?php if ($row["RequestCount"] > 0) { echo _n('%d pending request', '%d pending requests', $row["RequestCount"]); } ?></span></li>
				<li><a href="<?= get_pkgbase_uri($row['BaseName']) . 'request/'; ?>"><?= __('File Request'); ?></a></li>
				<?php if (has_credential(CRED_PKGBASE_DELETE)): ?>
				<li><a href="<?= get_pkgbase_uri($row['BaseName']) . 'delete/'; ?>"><?= __('Delete Package'); ?></a></li>
				<li><a href="<?= get_pkgbase_uri($row['BaseName']) . 'merge/'; ?>"><?= __('Merge Package'); ?></a></li>
				<?php endif; ?>
				<?php endif; ?>

				<?php if ($uid && $row["MaintainerUID"] === NULL): ?>
				<li>
					<form action="<?= get_pkgbase_uri($row['BaseName']) . 'adopt/'; ?>" method="post">
						<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
						<input type="submit" class="button text-button" name="do_Adopt" value="<?= __('Adopt Package') ?>" />
					</form>
				</li>
				<?php elseif (has_credential(CRED_PKGBASE_DISOWN, array($row["MaintainerUID"]))): ?>
				<li>
					<form action="<?= get_pkgbase_uri($row['BaseName']) . 'disown/'; ?>" method="post">
						<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
						<input type="submit" class="button text-button" name="do_Disown" value="<?= __('Disown Package') ?>" />
					</form>
				</li>
				<?php endif; ?>
			</ul>
		</div>
	</div>

	<table id="pkginfo">
		<tr>
			<th><?= __('Git Clone URL') . ': ' ?></th>
			<td>
				<a href="<?= $git_clone_uri_anon ?>"><?= $git_clone_uri_anon ?></a>
				<?php if ($uid == $row["MaintainerUID"]): ?>
				<br /> <a href="<?= $git_clone_uri_priv ?>"><?= $git_clone_uri_priv ?></a>
				<?php endif; ?>
			</td>
		</tr>
		<tr>
			<th><?= __('Package Base') . ': ' ?></th>
			<td class="wrap"><a href="<?= htmlspecialchars(get_pkgbase_uri($row['BaseName']), ENT_QUOTES); ?>"><?= htmlspecialchars($row['BaseName']); ?></a></td>
		</tr>
		<tr>
			<th><?= __('Description') . ': ' ?></th>
			<td class="wrap"><?= htmlspecialchars($row['Description']); ?></td>
		</tr>
		<tr>
			<th><?= __('Upstream URL') . ': ' ?></th>
			<td><a href="<?= htmlspecialchars($row['URL'], ENT_QUOTES) ?>" title="<?= __('Visit the website for') . ' ' . htmlspecialchars( $row['Name'])?>"><?= htmlspecialchars($row['URL'], ENT_QUOTES) ?></a></td>
		</tr>
<?php
if (has_credential(CRED_PKGBASE_SET_KEYWORDS, array($row["MaintainerUID"]))):
?>
		<tr>
			<th><?= __('Keywords') . ': ' ?></th>
			<td>
				<form method="post" action="<?= htmlspecialchars(get_pkgbase_uri($row['BaseName']), ENT_QUOTES); ?>">
					<div>
						<input type="hidden" name="action" value="do_SetKeywords" />
						<?php if ($SID): ?>
						<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
						<?php endif; ?>
						<input type="text" name="keywords" value="<?= htmlspecialchars(implode(" ", $keywords), ENT_QUOTES) ?>"/>
						<input type="submit" value="<?= __('Update') ?>"/>
					</div>
				</form>
			</td>
		</tr>
<?php endif; ?>
		<?php if (count($lics) > 0): ?>
		<tr>
			<th><?= __('Licenses') . ': ' ?></th>
			<td class="wrap">
				<?php foreach($lics as $lic): ?>
				<span class="related">
					<?php if ($lic !== end($lics)): ?>
					<?= htmlspecialchars($lic) ?>,
					<?php else: ?>
					<?= htmlspecialchars($lic) ?>
					<?php endif; ?>
				</span>
				<?php endforeach; ?>
			</td>
		</tr>
		<?php endif; ?>
		<?php if (count($grps) > 0): ?>
		<tr>
			<th><?= __('Groups') . ': ' ?></th>
			<td class="wrap">
				<?php foreach($grps as $grp): ?>
				<span class="related">
					<?php if ($grp !== end($grps)): ?>
					<?= htmlspecialchars($grp) ?>,
					<?php else: ?>
					<?= htmlspecialchars($grp) ?>
					<?php endif; ?>
				</span>
				<?php endforeach; ?>
			</td>
		</tr>
		<?php endif; ?>
		<?php if (count($rels_c) > 0): ?>
		<tr>
			<th><?= __('Conflicts') . ': ' ?></th>
			<td class="wrap relatedto">
				<?php foreach($rels_c as $rarr): ?>
				<span class="related">
					<?php if ($rarr !== end($rels_c)): ?>
					<?= pkg_rel_html($rarr[0], $rarr[2], $rarr[3]) ?>,
					<?php else: ?>
					<?= pkg_rel_html($rarr[0], $rarr[2], $rarr[3]) ?>
					<?php endif; ?>
				</span>
				<?php endforeach; ?>
			</td>
		</tr>
		<?php endif; ?>
		<?php if (count($rels_p) > 0): ?>
		<tr>
			<th><?= __('Provides') . ': ' ?></th>
			<td class="wrap relatedto">
				<?php foreach($rels_p as $rarr): ?>
				<span class="related">
					<?php if ($rarr !== end($rels_p)): ?>
					<?= pkg_rel_html($rarr[0], $rarr[2], $rarr[3]) ?>,
					<?php else: ?>
					<?= pkg_rel_html($rarr[0], $rarr[2], $rarr[3]) ?>
					<?php endif; ?>
				</span>
				<?php endforeach; ?>
			</td>
		</tr>
		<?php endif; ?>
		<?php if (count($rels_r) > 0): ?>
		<tr>
			<th><?= __('Replaces') . ': ' ?></th>
			<td class="wrap relatedto">
				<?php foreach($rels_r as $rarr): ?>
				<span class="related">
					<?php if ($rarr !== end($rels_r)): ?>
					<?= pkg_rel_html($rarr[0], $rarr[2], $rarr[3]) ?>,
					<?php else: ?>
					<?= pkg_rel_html($rarr[0], $rarr[2], $rarr[3]) ?>
					<?php endif; ?>
				</span>
				<?php endforeach; ?>
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
			<td><a href="<?= get_pkgbase_uri($row['BaseName']); ?>voters/"><?= $votes ?></a></td>
			<?php else: ?>
			<td><?= $votes ?></td>
			<?php endif; ?>
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
		<div id="pkgdeps" class="listing">
			<h3><?= __('Dependencies') . " (" . count($deps) . ")"?></h3>
<?php if (count($deps) > 0): ?>
			<ul id="pkgdepslist">
<?php while (list($k, $darr) = each($deps)): ?>
	<li><?= pkg_depend_link($darr[0], $darr[1], $darr[2], $darr[3], $darr[4]); ?></li>
<?php endwhile; ?>
			</ul>
<?php endif; ?>
		</div>
		<div id="pkgreqs" class="listing">
			<h3><?= __('Required by') . " (" . count($requiredby) . ")"?></h3>
<?php if (count($requiredby) > 0): ?>
			<ul id="pkgreqslist">
<?php
	# darr: (PackageName, PackageID)
	while (list($k, $darr) = each($requiredby)):
?>
				<li><a href="<?= htmlspecialchars(get_pkg_uri($darr[0]), ENT_QUOTES); ?>" title="<?= __('View packages details for').' ' . htmlspecialchars($darr[0]) ?>"><?= htmlspecialchars($darr[0]) ?></a></li>
	<?php endwhile; ?>
			</ul>
<?php endif; ?>
		</div>
		<div id="pkgfiles" class="listing">
			<h3><?= __('Sources') ?></h3>
		</div>
		<?php if (count($sources) > 0): ?>
		<div>
			<ul id="pkgsrcslist">
					<?php while (list($k, $src) = each($sources)): ?>
					<li><?= pkg_source_link($src[0], $src[1]) ?></li>
					<?php endwhile; ?>
			</ul>
		</div>
		<?php endif; ?>
	</div>
</div>
