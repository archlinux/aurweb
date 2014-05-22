<h3><?= __("Recent Updates") ?></h3>

<a href="<?= get_uri('/rss/') ?>" title="Arch Package Updates RSS Feed" class="rss-icon"><img src="/images/feed-icon-14x14.png" alt="RSS Feed" /></a>

<table>
	<tbody>
		<?php foreach ($newest_packages->getIterator() as $row): ?>
		<tr>
			<td class="pkg-name">
				<a href="<?= get_pkg_uri($row["Name"]); ?>" title="<?= htmlspecialchars($row["Name"]) . ' ' . htmlspecialchars($row["Version"]); ?>"><?= htmlspecialchars($row["Name"]) . ' ' . htmlspecialchars($row["Version"]); ?></a>
			</td>
			<td class="pkg-new">
				<?php if ($row["ModifiedTS"] === $row["SubmittedTS"]): ?>
				<img src="images/new.png" alt="New!" />
				<?php endif; ?>
			</td>
			<td class="pkg-date">
				<span><?= gmdate("Y-m-d H:i", intval($row["ModifiedTS"])); ?></span>
			</td>
		</tr>
		<?php endforeach; ?>
	</tbody>
</table>
