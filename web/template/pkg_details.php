<?php

$pkgbuild_uri = sprintf(config_get('options', 'pkgbuild_uri'), urlencode($row['BaseName']));
$log_uri = sprintf(config_get('options', 'log_uri'), urlencode($row['BaseName']));
$snapshot_uri = sprintf(config_get('options', 'snapshot_uri'), urlencode($row['BaseName']));
$git_clone_uri_anon = sprintf(config_get('options', 'git_clone_uri_anon'), htmlspecialchars($row['BaseName']));
$git_clone_uri_priv = sprintf(config_get('options', 'git_clone_uri_priv'), htmlspecialchars($row['BaseName']));
$max_depends = config_get_int('options', 'max_depends');

$uid = uid_from_sid($SID);

$pkgid = intval($row['ID']);
$base_id = intval($row['BaseID']);

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
$license = empty($row['License']) ? $msg : $row['License'];

# Print the timestamps for last updates
$updated_time = ($row["ModifiedTS"] == 0) ? $msg : date("Y-m-d H:i", intval($row["ModifiedTS"]));
$submitted_time = ($row["SubmittedTS"] == 0) ? $msg : date("Y-m-d H:i", intval($row["SubmittedTS"]));
$out_of_date_time = ($row["OutOfDateTS"] == 0) ? $msg : date("Y-m-d", intval($row["OutOfDateTS"]));

$lics = pkg_licenses($row["ID"]);
$grps = pkg_groups($row["ID"]);

$deps = pkg_dependencies($row["ID"], $max_depends);

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

$requiredby = pkg_required($row["Name"], $rels_p, $max_depends);

# $sources[0] = 'src';
$sources = pkg_sources($row["ID"]);

$base_uri = get_pkgbase_uri($row['BaseName']);

?>
<div id="pkgdetails" class="box">
	<h2><?= __('Package Details') . ': ' . htmlspecialchars($row['Name']) . ' ' . htmlspecialchars($row['Version']) ?></h2>

	<?php include('pkgbase_actions.php') ?>

	<table id="pkginfo">
		<tr>
			<th><?= __('Git Clone URL') . ': ' ?></th>
			<td>
				<a href="<?= $git_clone_uri_anon ?>"><?= $git_clone_uri_anon ?></a> (<?= __('read-only') ?>)
				<?php if (in_array($uid, $maintainers)): ?>
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
<?php if (!empty($row['Description'])): ?>
			<td class="wrap"><?= htmlspecialchars($row['Description']); ?></td>
<?php else: ?>
			<td class="wrap"><?= __('None') ?></td>
<?php endif; ?>
		</tr>
		<tr>
			<th><?= __('Upstream URL') . ': ' ?></th>
<?php if (!empty($row['URL'])): ?>
			<td><a href="<?= htmlspecialchars($row['URL'], ENT_QUOTES) ?>" title="<?= __('Visit the website for') . ' ' . htmlspecialchars( $row['Name'])?>"><?= htmlspecialchars($row['URL'], ENT_QUOTES) ?></a></td>
<?php else: ?>
			<td class="wrap"><?= __('None') ?></td>
<?php endif; ?>
		</tr>
<?php
if (has_credential(CRED_PKGBASE_SET_KEYWORDS, $maintainers) || count($keywords) > 0):
?>
		<tr>
			<th><?= __('Keywords') . ': ' ?></th>
			<td>
<?php
if (has_credential(CRED_PKGBASE_SET_KEYWORDS, $maintainers)):
?>
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
				<?php while (list($k, $darr) = each($requiredby)): ?>
				<li><?= pkg_requiredby_link($darr[0], $darr[1], $darr[2], $darr[3], $row['Name']); ?></li>
				<?php endwhile; ?>
			</ul>
<?php endif; ?>
		</div>
		<div id="pkgfiles" class="listing">
			<h3><?= __('Sources') . " (" . count($sources) . ")"?></h3>
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
