<h3><?php echo __("Recent Updates") ?></h3>

<a href="<?php echo get_uri('/rss/') ?>" title="Arch Package Updates RSS Feed" class="rss-icon"><img src="/images/feed-icon-14x14.png" alt="RSS Feed" /></a>

<table>
	<?php foreach ($newest_packages->getIterator() as $row): ?>
		<tr>
			<td>
				<a href="<?php echo get_pkg_uri($row["Name"]); ?>"><?php print htmlspecialchars($row["Name"]) . ' ' . htmlspecialchars($row["Version"]); ?></a>
				<?php if ($row["ModifiedTS"] === $row["SubmittedTS"]): ?>
				<img src="images/new.png" alt="New!" />
				<?php endif; ?>
			</td>
			<td>
				<span><?php print gmdate("Y-m-d H:i", intval($row["ModifiedTS"])); ?></span>
			</td>
		</tr>
	<?php endforeach; ?>
</table>
