<?php
if (isset($_COOKIE['AURSID'])) {
	$atype = account_from_sid($_COOKIE['AURSID']);
} else {
	$atype = "";
}

if (!$result): ?>
	<div class="box"><p><?php echo __("Error retrieving package list.") ?></p></div>
<?php elseif ($total == 0): ?>
	<div class="box"><p><?php echo __("No packages matched your search criteria.") ?></p></div>
<?php else: ?>
	<div id="pkglist-results" class="box">
		<div class="pkglist-stats">
			<p><?php echo __('%d packages found. Page %d of %d.', $total, $current, $pages) ?></p>
			<?php if (count($templ_pages) > 1): ?>
			<p class="pkglist-nav">
				<?php foreach ($templ_pages as $pagenr => $pagestart): ?>
					<?php if ($pagestart === false): ?>
						<span class="page"><?php echo $pagenr ?></span>
					<?php elseif ($pagestart + 1 == $first): ?>
						<span class="page"><?php echo $pagenr ?></span>
					<?php else: ?>
						<a class="page" href="<?php echo get_uri('/packages/'); ?>?<?php echo mkurl('O=' . $pagestart) ?>"><?php echo $pagenr ?></a>
					<?php endif; ?>
				<?php endforeach; ?>
			</p>
			<?php endif; ?>
		</div>

		<form id="pkglist-results-form" method="post" action="<?php echo get_uri('/packages/'); ?>?<?php echo htmlentities($_SERVER['QUERY_STRING']) ?>">
			<table class="results">
			<thead>
				<tr>
					<?php if ($SID): ?>
					<th>&nbsp;</th>
					<?php endif; ?>
					<th><a href="?<?php echo mkurl('SB=c&SO=' . $SO_next) ?>"><?php echo __("Category") ?></a></th>
					<th><a href="?<?php echo mkurl('SB=n&SO=' . $SO_next) ?>"><?php echo __("Name") ?></a></th>
					<th><a href="?<?php echo mkurl('SB=v&SO=' . $SO_next) ?>"><?php echo __("Votes") ?></a></th>
					<?php if ($SID): ?>
					<th><a href="?<?php echo mkurl('SB=w&SO=' . $SO_next) ?>"><?php echo __("Voted") ?></a></th>
					<th><a href="?<?php echo mkurl('SB=o&SO=' . $SO_next) ?>"><?php echo __("Notify") ?></a></th>
					<?php endif; ?>
					<th><?php echo __("Description") ?></th>
					<th><a href="?<?php echo mkurl('SB=m&SO=' . $SO_next) ?>"><?php echo __("Maintainer") ?></a></th>
				</tr>
			</thead>
			<tbody>

	<?php while (list($indx, $row) = each($searchresults)): ?>
		<tr class="<?php echo ($indx % 2 == 0) ? 'odd' : 'even' ?>">
		<?php if ($SID): ?>
		<td><input type="checkbox" name="IDs[<?php echo $row["ID"] ?>]" value="1" /></td>
		<?php endif; ?>
		<td><?php echo htmlspecialchars($row["Category"]) ?></td>
		<td><a href="<?php echo htmlspecialchars(get_pkg_uri($row["Name"]), ENT_QUOTES); ?>"><?php echo htmlspecialchars($row["Name"]) . ' ' . htmlspecialchars($row["Version"]) ?></a></td>
		<td><?php echo $row["NumVotes"] ?></td>
		<?php if ($SID): ?>
		<td>
		<?php if (isset($row["Voted"])): ?>
		<?php echo __("Yes") ?>
		<?php endif; ?>
		</td>
		<td>
		<?php if (isset($row["Notify"])): ?>
		<?php echo __("Yes") ?>
		<?php endif; ?>
		</td>
		<?php endif; ?>
		<td><?php echo htmlspecialchars($row['Description'], ENT_QUOTES); ?></td>
		<td>
		<?php if (isset($row["Maintainer"])): ?>
		<a href="<?php echo get_uri('/packages/'); ?>?K=<?php echo htmlspecialchars($row['Maintainer'], ENT_QUOTES) ?>&amp;SeB=m"><?php echo htmlspecialchars($row['Maintainer']) ?></a>
		<?php else: ?>
		<span><?php echo __("orphan") ?></span>
		<?php endif; ?>
		</td>
	</tr>
	<?php endwhile; ?>

			</tbody>
			</table>

			<div class="pkglist-stats">
				<p><?php echo __('%d packages found. Page %d of %d.', $total, $current, $pages) ?></p>
				<?php if (count($templ_pages) > 1): ?>
				<p class="pkglist-nav">
					<?php foreach ($templ_pages as $pagenr => $pagestart): ?>
						<?php if ($pagestart === false): ?>
							<span class="page"><?php echo $pagenr ?></span>
						<?php elseif ($pagestart + 1 == $first): ?>
							<span class="page"><?php echo $pagenr ?></span>
						<?php else: ?>
							<a class="page" href="<?php echo get_uri('/packages/'); ?>?<?php echo mkurl('O=' . $pagestart) ?>"><?php echo $pagenr ?></a>
						<?php endif; ?>
					<?php endforeach; ?>
				</p>
				<?php endif; ?>
			</div>

			<?php if ($SID): ?>
				<p>
					<select name="action">
						<option><?php echo __("Actions") ?></option>
						<option value="do_Flag"><?php echo __("Flag Out-of-date") ?></option>
						<option value="do_UnFlag"><?php echo __("Unflag Out-of-date") ?></option>
						<option value="do_Adopt"><?php echo __("Adopt Packages") ?></option>
						<option value="do_Disown"><?php echo __("Disown Packages") ?></option>
						<?php if ($atype == "Trusted User" || $atype == "Developer"): ?>
						<option value="do_Delete"><?php echo __("Delete Packages") ?></option>
						<?php endif; ?>
						<option value="do_Notify"><?php echo __("Notify") ?></option>
						<option value="do_UnNotify"><?php echo __("UnNotify") ?></option>
					</select>
					<?php if ($atype == "Trusted User" || $atype == "Developer"): ?>
						<label for="merge_Into"><?php echo __("Merge into") ?></label>
						<input type="text" id="merge_Into" name="merge_Into" />
						<input type="checkbox" name="confirm_Delete" value="1" /> <?php echo __("Confirm") ?>
					<?php endif; ?>
					<input type="hidden" name="token" value="<?php echo htmlspecialchars($_COOKIE['AURSID']) ?>" />
					<input type="submit" class="button" style="width: 80px" value="<?php echo __("Go") ?>" />
				</p>
			<?php endif; # if ($SID) ?>
		</form>
	</div>
<?php endif; # search was successful and returned multiple results ?>
