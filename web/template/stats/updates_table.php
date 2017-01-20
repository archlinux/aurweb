<h3><?= __("Recent Updates") ?> <span class="more">(<a href="<?= get_uri('/packages/') ?>?SB=l&amp;SO=d"><?= __('more') ?></a>)</span></h3>

<a href="<?= get_uri('/rss/') ?>" title="Arch Package Updates RSS Feed" class="rss-icon"><img src="/images/rss.svg" alt="RSS Feed" /></a>

<table>
	<tbody>
		<?php foreach ($newest_packages->getIterator() as $row): ?>
		<tr>
			<td class="pkg-name">
				<a href="<?= get_pkg_uri($row["Name"]); ?>" title="<?= htmlspecialchars($row["Name"]) . ' ' . htmlspecialchars($row["Version"]); ?>"><?= htmlspecialchars($row["Name"]) . ' ' . htmlspecialchars($row["Version"]); ?></a>
			</td>
			<td class="pkg-date">
				<span><?= date("Y-m-d H:i", intval($row["ModifiedTS"])); ?></span>
			</td>
		</tr>
		<?php endforeach; ?>
	</tbody>
</table>
