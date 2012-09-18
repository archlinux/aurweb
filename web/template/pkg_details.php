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
	<h2><?php echo __('Package Details') . ': ' . htmlspecialchars($row['Name']) . ' ' . htmlspecialchars($row['Version']) ?></h2>
	<div id="detailslinks" class="listing">
		<div id="actionlist">
			<h4>Package Actions</h4>
			<ul class="small">
				<li><a href="<?php echo $urlpath ?>/PKGBUILD"><?php echo __('View PKGBUILD') ?></a></li>
				<li><a href="<?php echo $urlpath . '/' . $row['Name'] ?>.tar.gz"><?php echo __('Download tarball') ?></a></li>
				<li><span class="flagged"><?php if ($row["OutOfDateTS"] !== NULL) { echo __('Flagged out-of-date')." (${out_of_date_time})"; } ?></span></li>
				<?php if ($USE_VIRTUAL_URLS && $uid): ?>
				<?php if ($row["OutOfDateTS"] === NULL): ?>
				<li><a href="<?php echo get_pkg_uri($row['Name']) . 'flag/'; ?>"><?php echo __('Flag package out-of-date'); ?></a></li>
				<?php elseif (($row["OutOfDateTS"] !== NULL) &&
				($uid == $row["MaintainerUID"] || $atype == "Trusted User" || $atype == "Developer")): ?>
				<li><a href="<?php echo get_pkg_uri($row['Name']) . 'unflag/'; ?>"><?php echo __('Unflag package'); ?></a></li>
				<?php endif; ?>
				<?php if (user_voted($uid, $row['ID'])): ?>
				<li><a href="<?php echo get_pkg_uri($row['Name']) . 'unvote/'; ?>"><?php echo __('Remove vote'); ?></a></li>
				<?php else: ?>
				<li><a href="<?php echo get_pkg_uri($row['Name']) . 'vote/'; ?>"><?php echo __('Vote for this package'); ?></a></li>
				<?php endif; ?>
				<?php if (user_notify($uid, $row['ID'])): ?>
				<li><a href="<?php echo get_pkg_uri($row['Name']) . 'unnotify/'; ?>"><?php echo __('Disable notifications'); ?></a></li>
				<?php else: ?>
				<li><a href="<?php echo get_pkg_uri($row['Name']) . 'notify/'; ?>"><?php echo __('Notify of new comments'); ?></a></li>
				<?php endif; ?>
				<?php endif; ?>
			</ul>
			<?php if ($uid): ?>
			<form action="<?php echo htmlspecialchars(get_pkg_uri($row['Name']), ENT_QUOTES); ?>" method="post">
				<div>
					<input type="hidden" name="IDs[<?php echo $row['ID'] ?>]" value="1" />
					<input type="hidden" name="ID" value="<?php echo $row['ID'] ?>" />
					<input type="hidden" name="token" value="<?php echo htmlspecialchars($_COOKIE['AURSID']) ?>" />
				</div>
				<p>
					<?php if ($row["MaintainerUID"] === NULL): ?>
						<input type="submit" class="button" name="do_Adopt" value="<?php echo __("Adopt Packages") ?>" />
					<?php elseif ($uid == $row["MaintainerUID"] ||
						$atype == "Trusted User" || $atype == "Developer"): ?>
						<input type="submit" class="button" name="do_Disown" value="<?php echo __("Disown Packages") ?>" />
					<?php endif; ?>
				</p>
			</form>
			<?php endif; ?>
		</div>
	</div>

	<table id="pkginfo">
		<tr>
			<th><?php echo __('Description') . ': ' ?></th>
			<td class="wrap"><?php echo htmlspecialchars($row['Description']); ?></td>
		</tr>
		<tr>
			<th>Upstream URL:</th>
			<td><a href="<?php echo htmlspecialchars($row['URL'], ENT_QUOTES) ?>" title="<?php echo __('Visit the website for') . ' ' . htmlspecialchars( $row['Name'])?>"><?php echo htmlspecialchars($row['URL'], ENT_QUOTES) ?></a></td>
		</tr>
		<tr>
			<th><?php echo __('Category') . ': ' ?></th>
<?php
if ($SID && ($uid == $row["MaintainerUID"] ||
	($atype == "Developer" || $atype == "Trusted User"))):
?>
			<td>
				<form method="post" action="<?php echo htmlspecialchars(get_pkg_uri($row['Name']), ENT_QUOTES); ?>">
					<div>
						<input type="hidden" name="action" value="do_ChangeCategory" />
						<?php if ($SID): ?>
						<input type="hidden" name="token" value="<?php echo htmlspecialchars($_COOKIE['AURSID']) ?>" />
						<?php endif; ?>
						<select name="category_id">
<?php
	foreach ($catarr as $cid => $catname):
?>
							<option value="<?php echo $cid ?>"<?php if ($cid == $row["CategoryID"]) { ?> selected="selected" <?php } ?>><?php echo $catname ?></option>
	<?php endforeach; ?>
						</select>
						<input type="submit" value="<?php echo __('Change category') ?>"/>
					</div>
				</form>
<?php else: ?>
			<td>
				<a href="<?php echo get_uri('/packages/'); ?>?C=<?php echo $row['CategoryID'] ?>"><?php print $row['Category'] ?></a>
<?php endif; ?>
			</td>
		<tr>
			<th><?php echo __('License') . ': ' ?></th>
			<td><?php echo htmlspecialchars($license) ?></td>
		</tr>
		<tr>
			<th><?php echo __('Submitter') .': ' ?></th>
<?php
if ($row["SubmitterUID"]):
	if ($SID):
?>
			<td><a href="<?php echo get_uri('/account/'); ?>?Action=AccountInfo&amp;ID=<?php echo htmlspecialchars($row['SubmitterUID'], ENT_QUOTES) ?>" title="<?php echo __('View account information for')?> <?php echo htmlspecialchars($submitter) ?>"><?php echo htmlspecialchars($submitter) ?></a></td>
<?php else: ?>
		<td><?php echo htmlspecialchars($submitter) ?></td>
	<?php endif; ?>
<?php else: ?>
			<td>None</td>
<?php endif; ?>
		<tr>
			<th><?php echo __('Maintainer') .': ' ?></th>
<?php
if ($row["MaintainerUID"]):
	if ($SID):
?>
			<td><a href="<?php echo get_uri('/account/'); ?>?Action=AccountInfo&amp;ID=<?php echo htmlspecialchars($row['MaintainerUID'], ENT_QUOTES) ?>" title="<?php echo __('View account information for')?> <?php echo htmlspecialchars($maintainer) ?>"><?php echo htmlspecialchars($maintainer) ?></a></td>
	<?php else: ?>
		<td><?php echo htmlspecialchars($maintainer) ?></td>
	<?php endif; ?>
<?php else: ?>
			<td>None</td>
<?php endif; ?>
		</tr>
		<tr>
			<th><?php echo __('Votes') . ': ' ?></th>
<?php if ($atype == "Developer" || $atype == "Trusted User"): ?>
<?php if ($USE_VIRTUAL_URLS): ?>
			<td><a href="<?php echo get_pkg_uri($row['Name']); ?>voters/"><?php echo $votes ?></a>
<?php else: ?>
			<td><a href="<?php echo get_uri('/voters/'); ?>?ID=<?php echo $pkgid ?>"><?php echo $votes ?></a>
<?php endif; ?>
<?php else: ?>
			<td><?php echo $votes ?></td>
<?php endif; ?>
		</tr>
		<tr>
			<th><?php echo __('First Submitted') . ': ' ?></th>
			<td><?php echo $submitted_time ?></td>
		</tr>
		<tr>
			<th><?php echo __('Last Updated') . ': ' ?></th>
			<td><?php echo $updated_time ?></td>
		</tr>
	</table>

	<div id="metadata">
		<div id="pkgdeps" class="listing">
			<h3><?php echo __('Dependencies') . " (" . count($deps) . ")"?></h3>
<?php if (count($deps) > 0): ?>
			<ul>
<?php
	while (list($k, $darr) = each($deps)):
		# darr: (DepName, DepCondition, PackageID), where ID is NULL if it didn't exist
		if (!is_null($darr[2])):
?>
				<li><a href="<?php echo htmlspecialchars(get_pkg_uri($darr[0]), ENT_QUOTES); ?>" title="<?php echo __('View packages details for').' '.$darr[0].$darr[1]?>"><?php echo $darr[0].$darr[1]?></a></li>
		<?php else: ?>
				<li><a href="http://www.archlinux.org/packages/?q=<?php echo urlencode($darr[0])?>" title="<?php echo __('View packages details for').' '.$darr[0].$darr[1] ?>"><?php echo $darr[0].$darr[1] ?></a></li>
		<?php endif; ?>
	<?php endwhile; ?>
			</ul>
<?php endif; ?>
		</div>
		<div id="pkgreqs" class="listing">
			<h3><?php echo __('Required by') . " (" . count($requiredby) . ")"?></h3>
<?php if (count($requiredby) > 0): ?>
			<ul>
<?php
	# darr: (PackageName, PackageID)
	while (list($k, $darr) = each($requiredby)):
?>
				<li><a href="<?php echo htmlspecialchars(get_pkg_uri($darr[0]), ENT_QUOTES); ?>" title="<?php echo __('View packages details for').' '.$darr[0]?>"><?php echo $darr[0] ?></a></li>
	<?php endwhile; ?>
			</ul>
<?php endif; ?>
		</div>
		<div id="pkgfiles" class="listing">
			<h3><?php echo __('Sources') ?></h3>
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
				<li><a href="<?php echo htmlspecialchars((isset($src[1]) ? $src[1] : $src[0]), ENT_QUOTES) ?>"><?php echo htmlspecialchars($src[0]) ?> </a></li>
<?php
		else:
			# It is presumably an internal source
			$src = $src[0];
?>
				<li><?php echo htmlspecialchars($src) ?></li>
		<?php endif; ?>
	<?php endwhile; ?>
			</ul>
		</div>
<?php endif; ?>
	</div>
</div>
