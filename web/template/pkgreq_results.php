<div id="pkglist-results" class="box">
	<div class="pkglist-stats">
		<p><?= __('%d package requests found. Page %d of %d.', $total, $current, $pages) ?></p>
		<?php if (count($templ_pages) > 1): ?>
		<p class="pkglist-nav">
			<?php foreach ($templ_pages as $pagenr => $pagestart): ?>
				<?php if ($pagestart === false): ?>
					<span class="page"><?= $pagenr ?></span>
				<?php elseif ($pagestart + 1 == $first): ?>
					<span class="page"><?= $pagenr ?></span>
				<?php else: ?>
					<a class="page" href="<?= get_uri('/requests/'); ?>?<?= mkurl('O=' . $pagestart) ?>"><?= $pagenr ?></a>
				<?php endif; ?>
			<?php endforeach; ?>
		</p>
		<?php endif; ?>
	</div>

	<table class="results">
	<thead>
		<tr>
			<th><?= __("Package") ?></th>
			<th><?= __("Type") ?></th>
			<th><?= __("Comments") ?></th>
			<th><?= __("Filed by") ?></th>
			<th><?= __("Date") ?></th>
		</tr>
	</thead>
	<tbody>

		<?php while (list($indx, $row) = each($results)): ?>
		<tr class="<?= ($indx % 2 == 0) ? 'odd' : 'even' ?>">
			<?php if ($row['BaseID']): ?>
			<td><a href="<?= htmlspecialchars(get_pkgbase_uri($row["Name"]), ENT_QUOTES); ?>"><?= htmlspecialchars($row["Name"]) ?></a></td>
			<?php else: ?>
			<td><?= htmlspecialchars($row["Name"]) ?></td>
			<?php endif; ?>
			<td><?= htmlspecialchars(ucfirst($row['Type']), ENT_QUOTES); ?></td>
			<td class="wrap"><?= htmlspecialchars($row['Comments'], ENT_QUOTES); ?></td>
			<td>
			<a href="<?= get_uri('/account/') . htmlspecialchars($row['User'], ENT_QUOTES) ?>" title="<?= __('View account information for %s', htmlspecialchars($row['User'])) ?>"><?= htmlspecialchars($row['User']) ?></a>
			</td>
			<td><?= gmdate("Y-m-d H:i", intval($row['RequestTS'])) ?></td>
		</tr>
		<?php endwhile; ?>

	</tbody>
	</table>

	<div class="pkglist-stats">
		<p><?= __('%d package requests found. Page %d of %d.', $total, $current, $pages) ?></p>
		<?php if (count($templ_pages) > 1): ?>
		<p class="pkglist-nav">
			<?php foreach ($templ_pages as $pagenr => $pagestart): ?>
				<?php if ($pagestart === false): ?>
					<span class="page"><?= $pagenr ?></span>
				<?php elseif ($pagestart + 1 == $first): ?>
					<span class="page"><?= $pagenr ?></span>
				<?php else: ?>
					<a class="page" href="<?= get_uri('/requests/'); ?>?<?= mkurl('O=' . $pagestart) ?>"><?= $pagenr ?></a>
				<?php endif; ?>
			<?php endforeach; ?>
		</p>
		<?php endif; ?>
	</div>
</div>
