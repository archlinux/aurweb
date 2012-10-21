<?php
$atype = account_from_sid($SID);
$uid = uid_from_sid($SID);

$pkgid = intval($row['ID']);

$catarr = pkgCategories();

$submitter = username_from_id($row["SubmitterUID"]);
$maintainer = username_from_id($row["MaintainerUID"]);

$votes = $row['NumVotes'];

# In case of wanting to put a custom message
$msg = __('unknown');
$license = empty($row['License']) ? $msg : $row['License'];

# Print the timestamps for last updates
$updated_time = ($row["ModifiedTS"] == 0) ? $msg : gmdate("Y-m-d H:i", intval($row["ModifiedTS"]));
$submitted_time = ($row["SubmittedTS"] == 0) ? $msg : gmdate("Y-m-d H:i", intval($row["SubmittedTS"]));
$out_of_date_time = ($row["OutOfDateTS"] == 0) ? $msg : gmdate("Y-m-d", intval($row["OutOfDateTS"]));

$urlpath = URL_DIR . substr($row['Name'], 0, 2) . "/" . $row['Name'];

$deps = package_dependencies($row["ID"]);
$requiredby = package_required($row["Name"]);

# $sources[0] = 'src';
$sources = package_sources($row["ID"]);
?>
<div id="pkgdetails" class="box">
	<h2><?= __('Package Details') . ': ' . htmlspecialchars($row['Name']) . ' ' . htmlspecialchars($row['Version']) ?></h2>
	<div id="detailslinks" class="listing">
		<div id="actionlist">
			<h4>Package Actions</h4>
			<ul class="small">
				<li><a href="<?= $urlpath ?>/PKGBUILD"><?= __('View PKGBUILD') ?></a></li>
				<li><a href="<?= $urlpath . '/' . $row['Name'] ?>.tar.gz"><?= __('Download tarball') ?></a></li>
				<li><span class="flagged"><?php if ($row["OutOfDateTS"] !== NULL) { echo __('Flagged out-of-date')." (${out_of_date_time})"; } ?></span></li>
				<?php if ($USE_VIRTUAL_URLS && $uid): ?>
				<?php if ($row["OutOfDateTS"] === NULL): ?>
				<li><a href="<?= get_pkg_uri($row['Name']) . 'flag/'; ?>"><?= __('Flag package out-of-date'); ?></a></li>
				<?php elseif (($row["OutOfDateTS"] !== NULL) &&
				($uid == $row["MaintainerUID"] || $atype == "Trusted User" || $atype == "Developer")): ?>
				<li><a href="<?= get_pkg_uri($row['Name']) . 'unflag/'; ?>"><?= __('Unflag package'); ?></a></li>
				<?php endif; ?>
				<?php if (user_voted($uid, $row['ID'])): ?>
				<li><a href="<?= get_pkg_uri($row['Name']) . 'unvote/'; ?>"><?= __('Remove vote'); ?></a></li>
				<?php else: ?>
				<li><a href="<?= get_pkg_uri($row['Name']) . 'vote/'; ?>"><?= __('Vote for this package'); ?></a></li>
				<?php endif; ?>
				<?php if (user_notify($uid, $row['ID'])): ?>
				<li><a href="<?= get_pkg_uri($row['Name']) . 'unnotify/'; ?>"><?= __('Disable notifications'); ?></a></li>
				<?php else: ?>
				<li><a href="<?= get_pkg_uri($row['Name']) . 'notify/'; ?>"><?= __('Notify of new comments'); ?></a></li>
				<?php endif; ?>
				<?php if ($atype == "Trusted User" || $atype == "Developer"): ?>
				<li><a href="<?= get_pkg_uri($row['Name']) . 'delete/'; ?>"><?= __('Delete Package'); ?></a></li>
				<li><a href="<?= get_pkg_uri($row['Name']) . 'merge/'; ?>"><?= __('Merge Package'); ?></a></li>
				<?php endif; ?>
				<?php endif; ?>
			</ul>
			<?php if ($uid): ?>
			<form action="<?= htmlspecialchars(get_pkg_uri($row['Name']), ENT_QUOTES); ?>" method="post">
				<div>
					<input type="hidden" name="IDs[<?= $row['ID'] ?>]" value="1" />
					<input type="hidden" name="ID" value="<?= $row['ID'] ?>" />
					<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
				</div>
				<p>
					<?php if ($row["MaintainerUID"] === NULL): ?>
						<input type="submit" class="button" name="do_Adopt" value="<?= __("Adopt Packages") ?>" />
					<?php elseif ($uid == $row["MaintainerUID"] ||
						$atype == "Trusted User" || $atype == "Developer"): ?>
						<input type="submit" class="button" name="do_Disown" value="<?= __("Disown Packages") ?>" />
					<?php endif; ?>
				</p>
			</form>
			<?php endif; ?>
		</div>
	</div>

	<table id="pkginfo">
		<tr>
			<th><?= __('Description') . ': ' ?></th>
			<td class="wrap"><?= htmlspecialchars($row['Description']); ?></td>
		</tr>
		<tr>
			<th>Upstream URL:</th>
			<td><a href="<?= htmlspecialchars($row['URL'], ENT_QUOTES) ?>" title="<?= __('Visit the website for') . ' ' . htmlspecialchars( $row['Name'])?>"><?= htmlspecialchars($row['URL'], ENT_QUOTES) ?></a></td>
		</tr>
		<tr>
			<th><?= __('Category') . ': ' ?></th>
<?php
if ($SID && ($uid == $row["MaintainerUID"] ||
	($atype == "Developer" || $atype == "Trusted User"))):
?>
			<td>
				<form method="post" action="<?= htmlspecialchars(get_pkg_uri($row['Name']), ENT_QUOTES); ?>">
					<div>
						<input type="hidden" name="action" value="do_ChangeCategory" />
						<?php if ($SID): ?>
						<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
						<?php endif; ?>
						<select name="category_id">
<?php
	foreach ($catarr as $cid => $catname):
?>
							<option value="<?= $cid ?>"<?php if ($cid == $row["CategoryID"]) { ?> selected="selected" <?php } ?>><?= $catname ?></option>
	<?php endforeach; ?>
						</select>
						<input type="submit" value="<?= __('Change category') ?>"/>
					</div>
				</form>
<?php else: ?>
			<td>
				<a href="<?= get_uri('/packages/'); ?>?C=<?= $row['CategoryID'] ?>"><?= $row['Category'] ?></a>
<?php endif; ?>
			</td>
		</tr>
		<tr>
			<th><?= __('License') . ': ' ?></th>
			<td><?= htmlspecialchars($license) ?></td>
		</tr>
		<tr>
			<th><?= __('Submitter') .': ' ?></th>
<?php
if ($row["SubmitterUID"]):
	if ($SID):
		if (!$USE_VIRTUAL_URLS):
?>
			<td><a href="<?= get_uri('/account/'); ?>?Action=AccountInfo&amp;ID=<?= htmlspecialchars($row['SubmitterUID'], ENT_QUOTES) ?>" title="<?= __('View account information for')?> <?= htmlspecialchars($submitter) ?>"><?= htmlspecialchars($submitter) ?></a></td>
		<?php else: ?>
			<td><a href="<?= get_uri('/account/') . htmlspecialchars($submitter, ENT_QUOTES) ?>" title="<?= __('View account information for %s', htmlspecialchars($submitter)) ?>"><?= htmlspecialchars($submitter) ?></a></td>
		<?php endif; ?>
<?php else: ?>
		<td><?= htmlspecialchars($submitter) ?></td>
	<?php endif; ?>
<?php else: ?>
			<td>None</td>
<?php endif; ?>
		</tr>
		<tr>
			<th><?= __('Maintainer') .': ' ?></th>
<?php
if ($row["MaintainerUID"]):
	if ($SID):
		if (!$USE_VIRTUAL_URLS):
?>
			<td><a href="<?= get_uri('/account/'); ?>?Action=AccountInfo&amp;ID=<?= htmlspecialchars($row['MaintainerUID'], ENT_QUOTES) ?>" title="<?= __('View account information for')?> <?= htmlspecialchars($maintainer) ?>"><?= htmlspecialchars($maintainer) ?></a></td>
		<?php else: ?>
			<td><a href="<?= get_uri('/account/') . htmlspecialchars($maintainer, ENT_QUOTES) ?>" title="<?= __('View account information for %s', htmlspecialchars($maintainer)) ?>"><?= htmlspecialchars($maintainer) ?></a></td>
		<?php endif; ?>
	<?php else: ?>
		<td><?= htmlspecialchars($maintainer) ?></td>
	<?php endif; ?>
<?php else: ?>
			<td>None</td>
<?php endif; ?>
		</tr>
		<tr>
			<th><?= __('Votes') . ': ' ?></th>
<?php if ($atype == "Developer" || $atype == "Trusted User"): ?>
<?php if ($USE_VIRTUAL_URLS): ?>
			<td><a href="<?= get_pkg_uri($row['Name']); ?>voters/"><?= $votes ?></a></td>
<?php else: ?>
			<td><a href="<?= get_uri('/voters/'); ?>?ID=<?= $pkgid ?>"><?= $votes ?></a></td>
<?php endif; ?>
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
			<ul>
<?php
	while (list($k, $darr) = each($deps)):
		# darr: (DepName, DepCondition, PackageID), where ID is NULL if it didn't exist
		if (!is_null($darr[2])):
?>
				<li><a href="<?= htmlspecialchars(get_pkg_uri($darr[0]), ENT_QUOTES); ?>" title="<?= __('View packages details for').' '.$darr[0].$darr[1]?>"><?= $darr[0].$darr[1]?></a></li>
		<?php else: ?>
				<li><a href="https://www.archlinux.org/packages/?q=<?= urlencode($darr[0])?>" title="<?= __('View packages details for').' '.$darr[0].$darr[1] ?>"><?= $darr[0].$darr[1] ?></a></li>
		<?php endif; ?>
	<?php endwhile; ?>
			</ul>
<?php endif; ?>
		</div>
		<div id="pkgreqs" class="listing">
			<h3><?= __('Required by') . " (" . count($requiredby) . ")"?></h3>
<?php if (count($requiredby) > 0): ?>
			<ul>
<?php
	# darr: (PackageName, PackageID)
	while (list($k, $darr) = each($requiredby)):
?>
				<li><a href="<?= htmlspecialchars(get_pkg_uri($darr[0]), ENT_QUOTES); ?>" title="<?= __('View packages details for').' '.$darr[0]?>"><?= $darr[0] ?></a></li>
	<?php endwhile; ?>
			</ul>
<?php endif; ?>
		</div>
		<div id="pkgfiles" class="listing">
			<h3><?= __('Sources') ?></h3>
		</div>
<?php if (count($sources) > 0): ?>
		<div>
			<ul>
<?php
	while (list($k, $src) = each($sources)):
		$src = explode('::', $src);
		$parsed_url = parse_url($src[0]);

		# It is an external source
		if (isset($parsed_url['scheme']) || isset($src[1])):
?>
				<li><a href="<?= htmlspecialchars((isset($src[1]) ? $src[1] : $src[0]), ENT_QUOTES) ?>"><?= htmlspecialchars($src[0]) ?> </a></li>
<?php
		else:
			# It is presumably an internal source
			$src = $src[0];
?>
				<li><?= htmlspecialchars($src) ?></li>
		<?php endif; ?>
	<?php endwhile; ?>
			</ul>
		</div>
<?php endif; ?>
	</div>
</div>
