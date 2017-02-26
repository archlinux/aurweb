<div class="box">
	<h2><?= $type ?></h2>

	<?php if ($type == __("Current Votes")): ?>
	<ul class="admin-actions">
		<li><a href="<?= get_uri('/addvote/'); ?>"><?= __("Add Proposal") ?></a></li>
	</ul>
	<?php endif; ?>

	<?php if (empty($result)): ?>
	<p><?= __("No results found.") ?></p>
	<?php else: ?>
	<table class="results">
		<thead>
			<tr>
				<th><?= __("Proposal") ?></th>
				<th><a href="?off=<?= $off ?>&amp;by=<?= $by_next ?>"><?= __("Start") ?></a></th>
				<th><?= __("End") ?></th>
				<th><?= __("User") ?></th>
				<?php if ($type != __("Current Votes")): ?>
				<th><?= __("Yes") ?></th>
				<th><?= __("No") ?></th>
				<?php endif; ?>
				<th><?= __('Voted') ?></th>
			</tr>
		</thead>

		<tbody>
			<?php while (list($indx, $row) = each($result)): ?>
			<?php
			if ($indx % 2) {
				$c = "even";
			} else {
				$c = "odd";
			}
			?>
			<tr class="<?= $c ?>">
				<td><?php $row["Agenda"] = htmlspecialchars(substr($row["Agenda"], 0, $prev_Len)); ?>
					<a href="<?= get_uri('/tu/'); ?>?id=<?= $row['ID'] ?>"><?= $row["Agenda"] ?></a>
				</td>
				<td><?= date("Y-m-d", $row["Submitted"]) ?></td>
				<td><?= date("Y-m-d", $row["End"]) ?></td>
				<td>
				<?php if (!empty($row['User'])): ?>
					<a href="<?= get_uri('/packages/'); ?>?K=<?= $row['User'] ?>&amp;SeB=m"><?= $row['User'] ?></a>
				<?php else:
					print "N/A";
				endif;
				?>
				</td>
				<?php if ($type != __("Current Votes")): ?>
				<td><?= $row['Yes'] ?></td>
				<td><?= $row['No'] ?></td>
				<?php endif; ?>
				<td>
					<?php if (tu_voted($row['ID'], uid_from_sid($_COOKIE["AURSID"]))): ?>
					<span style="color: green; font-weight: bold"><?= __("Yes") ?></span>
					<?php else: ?>
					<span style="color: red; font-weight: bold"><?= __("No") ?></span>
					<?php endif; ?>
				</td>
			</tr>
			<?php endwhile; ?>
		</tbody>
	</table>

	<div class="pkglist-stats">
		<p class="pkglist-nav">
		<?php if ($result):
			$by = htmlentities($by, ENT_QUOTES); ?>
			<?php if ($nextresult > 0 && $off != 0):
				$back = (($off - $limit) <= 0) ? 0 : $off - $limit; ?>
				<a class="page" href='<?= get_uri('/tu/'); ?>?off=<?= $back ?>&amp;by=<?= $by ?>'>&lsaquo; <?= __("Back") ?></a>
			<?php endif; ?>
			<?php if (($off + $limit) < $nextresult):
				$forw = $off + $limit; ?>
			<a class="page" href="<?= get_uri('/tu/'); ?>?off=<?= $forw ?>&amp;by=<?= $by ?>"><?= __("Next") ?> &rsaquo;</a>
			<?php endif; ?>
		<?php endif; ?>
	</div>
	<?php endif; ?>
</div>
