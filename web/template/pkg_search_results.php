<?php
if (isset($_COOKIE['AURSID'])) {
	$atype = account_from_sid($_COOKIE['AURSID']);
} else {
	$atype = "";
}

if (!$result): ?>
	<div class="box"><p><?= __("Error retrieving package list.") ?></p></div>
<?php elseif ($total == 0): ?>
	<div class="box"><p><?= __("No packages matched your search criteria.") ?></p></div>
<?php else: ?>
	<div id="pkglist-results" class="box">
		<div class="pkglist-stats">
			<p><?= __('%d packages found. Page %d of %d.', $total, $current, $pages) ?></p>
			<?php if (count($templ_pages) > 1): ?>
			<p class="pkglist-nav">
				<?php foreach ($templ_pages as $pagenr => $pagestart): ?>
					<?php if ($pagestart === false): ?>
						<span class="page"><?= $pagenr ?></span>
					<?php elseif ($pagestart + 1 == $first): ?>
						<span class="page"><?= $pagenr ?></span>
					<?php else: ?>
						<a class="page" href="<?= get_uri('/packages/'); ?>?<?= mkurl('O=' . $pagestart) ?>"><?= $pagenr ?></a>
					<?php endif; ?>
				<?php endforeach; ?>
			</p>
			<?php endif; ?>
		</div>

		<form id="pkglist-results-form" method="post" action="<?= get_uri('/packages/'); ?>?<?= htmlentities($_SERVER['QUERY_STRING']) ?>">
			<table class="results">
			<thead>
				<tr>
					<?php if ($SID): ?>
					<th>&nbsp;</th>
					<?php endif; ?>
					<th><a href="?<?= mkurl('SB=c&SO=' . $SO_next) ?>"><?= __("Category") ?></a></th>
					<th><a href="?<?= mkurl('SB=n&SO=' . $SO_next) ?>"><?= __("Name") ?></a></th>
					<th><?= __("Version") ?></th>
					<th><a href="?<?= mkurl('SB=v&SO=' . $SO_next) ?>"><?= __("Votes") ?></a></th>
					<?php if ($SID): ?>
					<th><a href="?<?= mkurl('SB=w&SO=' . $SO_next) ?>"><?= __("Voted") ?></a></th>
					<th><a href="?<?= mkurl('SB=o&SO=' . $SO_next) ?>"><?= __("Notify") ?></a></th>
					<?php endif; ?>
					<th><?= __("Description") ?></th>
					<th><a href="?<?= mkurl('SB=m&SO=' . $SO_next) ?>"><?= __("Maintainer") ?></a></th>
				</tr>
			</thead>
			<tbody>

	<?php while (list($indx, $row) = each($searchresults)): ?>
		<tr class="<?= ($indx % 2 == 0) ? 'odd' : 'even' ?>">
		<?php if ($SID): ?>
		<td><input type="checkbox" name="IDs[<?= $row["ID"] ?>]" value="1" /></td>
		<?php endif; ?>
		<td><?= htmlspecialchars($row["Category"]) ?></td>
		<td><a href="<?= htmlspecialchars(get_pkg_uri($row["Name"]), ENT_QUOTES); ?>"><?= htmlspecialchars($row["Name"]) ?></a></td>
		<td><?= htmlspecialchars($row["Version"]) ?></td>
		<td><?= $row["NumVotes"] ?></td>
		<?php if ($SID): ?>
		<td>
		<?php if (isset($row["Voted"])): ?>
		<?= __("Yes") ?>
		<?php endif; ?>
		</td>
		<td>
		<?php if (isset($row["Notify"])): ?>
		<?= __("Yes") ?>
		<?php endif; ?>
		</td>
		<?php endif; ?>
		<td class="wrap"><?= htmlspecialchars($row['Description'], ENT_QUOTES); ?></td>
		<td>
		<?php if (isset($row["Maintainer"])): ?>
		<a href="<?= get_uri('/packages/'); ?>?K=<?= htmlspecialchars($row['Maintainer'], ENT_QUOTES) ?>&amp;SeB=m"><?= htmlspecialchars($row['Maintainer']) ?></a>
		<?php else: ?>
		<span><?= __("orphan") ?></span>
		<?php endif; ?>
		</td>
	</tr>
	<?php endwhile; ?>

			</tbody>
			</table>

			<div class="pkglist-stats">
				<p><?= __('%d packages found. Page %d of %d.', $total, $current, $pages) ?></p>
				<?php if (count($templ_pages) > 1): ?>
				<p class="pkglist-nav">
					<?php foreach ($templ_pages as $pagenr => $pagestart): ?>
						<?php if ($pagestart === false): ?>
							<span class="page"><?= $pagenr ?></span>
						<?php elseif ($pagestart + 1 == $first): ?>
							<span class="page"><?= $pagenr ?></span>
						<?php else: ?>
							<a class="page" href="<?= get_uri('/packages/'); ?>?<?= mkurl('O=' . $pagestart) ?>"><?= $pagenr ?></a>
						<?php endif; ?>
					<?php endforeach; ?>
				</p>
				<?php endif; ?>
			</div>

			<?php if ($SID): ?>
				<p>
					<select name="action">
						<option><?= __("Actions") ?></option>
						<option value="do_Flag"><?= __("Flag Out-of-date") ?></option>
						<option value="do_UnFlag"><?= __("Unflag Out-of-date") ?></option>
						<option value="do_Adopt"><?= __("Adopt Packages") ?></option>
						<option value="do_Disown"><?= __("Disown Packages") ?></option>
						<?php if ($atype == "Trusted User" || $atype == "Developer"): ?>
						<option value="do_Delete"><?= __("Delete Packages") ?></option>
						<?php endif; ?>
						<option value="do_Notify"><?= __("Notify") ?></option>
						<option value="do_UnNotify"><?= __("UnNotify") ?></option>
					</select>
					<?php if ($atype == "Trusted User" || $atype == "Developer"): ?>
						<label for="merge_Into"><?= __("Merge into") ?></label>
						<input type="text" id="merge_Into" name="merge_Into" />
						<input type="checkbox" name="confirm_Delete" value="1" /> <?= __("Confirm") ?>
					<?php endif; ?>
					<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
					<input type="submit" class="button" style="width: 80px" value="<?= __("Go") ?>" />
				</p>
			<?php endif; # if ($SID) ?>
		</form>
	</div>
<?php endif; # search was successful and returned multiple results ?>
