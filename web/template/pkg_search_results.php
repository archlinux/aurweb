<?php
if (!$result): ?>
	<div class="box"><p><?= __("Error retrieving package list.") ?></p></div>
<?php elseif ($total == 0): ?>
	<div class="box"><p><?= __("No packages matched your search criteria.") ?></p></div>
<?php else: ?>
	<div id="pkglist-results" class="box">
		<?php if ($show_headers): ?>
		<div class="pkglist-stats">
			<p>
				<?= _n('%d package found.', '%d packages found.', $total) ?>
				<?= __('Page %d of %d.', $current, $pages) ?>
			</p>
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
		<?php endif; ?>

		<form id="pkglist-results-form" method="post" action="<?= get_uri('/pkgbase/'); ?>?<?= htmlentities($_SERVER['QUERY_STRING']) ?>">
			<table class="results">
			<thead>
				<tr>
					<?php if ($SID && $show_headers): ?>
					<th>&nbsp;</th>
					<?php endif; ?>
					<th><a href="?<?= mkurl('SB=n&SO=' . $SO_next) ?>"><?= __("Name") ?></a></th>
					<th><?= __("Version") ?></th>
					<th><a href="?<?= mkurl('SB=v&SO=' . $SO_next) ?>"><?= __("Votes") ?></a></th>
					<th><a href="?<?= mkurl('SB=p&SO=' . $SO_next) ?>"><?= __("Popularity") ?></a><span title="<?= __('Popularity is calculated as the sum of all votes with each vote being weighted with a factor of %.2f per day since its creation.', 0.98) ?>" class="hover-help"><sup>?</sup></span></th>
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
		<?php if ($SID && $show_headers): ?>
		<td><input type="checkbox" name="IDs[<?= $row["PackageBaseID"] ?>]" value="1" /></td>
		<?php endif; ?>
		<td><a href="<?= htmlspecialchars(get_pkg_uri($row["Name"]), ENT_QUOTES); ?>"><?= htmlspecialchars($row["Name"]) ?></a></td>
		<td<?php if ($row["OutOfDateTS"]): ?> class="flagged"<?php endif; ?>><?= htmlspecialchars($row["Version"]) ?></td>
		<td><?= $row["NumVotes"] ?></td>
		<td><?= number_format($row["Popularity"], 2) ?></td>
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
		<?php if ($SID): ?>
		<a href="<?= get_uri('/account/') . htmlspecialchars($row['Maintainer'], ENT_QUOTES) ?>" title="<?= __('View account information for %s', htmlspecialchars($row['Maintainer'])) ?>"><?= htmlspecialchars($row['Maintainer']) ?></a>
		<?php else: ?>
		<a href="<?= get_uri('/packages/'); ?>?K=<?= htmlspecialchars($row['Maintainer'], ENT_QUOTES) ?>&amp;SeB=m"><?= htmlspecialchars($row['Maintainer']) ?></a>
		<?php endif; ?>
		<?php else: ?>
		<span><?= __("orphan") ?></span>
		<?php endif; ?>
		</td>
	</tr>
	<?php endwhile; ?>

			</tbody>
			</table>

			<?php if ($show_headers): ?>
			<div class="pkglist-stats">
				<p>
					<?= _n('%d package found.', '%d packages found.', $total) ?>
					<?= __('Page %d of %d.', $current, $pages) ?>
				</p>
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
						<option value="do_UnFlag"><?= __("Unflag Out-of-date") ?></option>
						<option value="do_Adopt"><?= __("Adopt Packages") ?></option>
						<option value="do_Disown"><?= __("Disown Packages") ?></option>
						<?php if (has_credential(CRED_PKGBASE_DELETE)): ?>
						<option value="do_Delete"><?= __("Delete Packages") ?></option>
						<?php endif; ?>
						<option value="do_Notify"><?= __("Notify") ?></option>
						<option value="do_UnNotify"><?= __("UnNotify") ?></option>
					</select>
					<?php if (has_credential(CRED_PKGBASE_DELETE)): ?>
						<label for="merge_Into"><?= __("Merge into") ?></label>
						<input type="text" id="merge_Into" name="merge_Into" />
					<?php endif; ?>
					<label class="confirmation"><input type="checkbox" name="confirm" value="1" /> <?= __("Confirm") ?></label>
					<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
					<input type="submit" class="button" style="width: 80px" value="<?= __("Go") ?>" />
				</p>
			<?php endif; # if ($SID) ?>
			<?php endif; ?>
		</form>
	</div>
<?php endif; # search was successful and returned multiple results ?>
