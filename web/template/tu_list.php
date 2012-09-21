<div class="box">
	<h2><?= $type ?></h2>
	<table class="results">
		<thead>
			<tr>
				<th><?= __("Proposal") ?></th>
				<th><a href="?off=<?= $off ?>&amp;by=<?= $by_next ?>"><?= __("Start") ?></a></th>
				<th><?= __("End") ?></th>
				<th><?= __("User") ?></th>
				<th><?= __("Yes") ?></th>
				<th><?= __("No") ?></th>
				<th><?= __('Voted') ?></th>
			</tr>
		</thead>

		<tbody>
			<?php if (empty($result)): ?>
			<tr><td align="center" colspan="0"><?= __("No results found.") ?></td></tr>
			<?php else: while (list($indx, $row) = each($result)):
				if ($indx % 2):
					$c = "even";
				else:
					$c = "odd";
				endif;
			?>
			<tr class="<?= $c ?>">
				<td><?php $row["Agenda"] = htmlspecialchars(substr($row["Agenda"], 0, $prev_Len)); ?>
					<a href="<?= get_uri('/tu/'); ?>?id=<?= $row['ID'] ?>"><?= $row["Agenda"] ?></a></span></span>
				</td>
				<td><?= gmdate("Y-m-d", $row["Submitted"]) ?></td>
				<td><?= gmdate("Y-m-d", $row["End"]) ?></td>
				<td>
				<?php if (!empty($row['User'])): ?>
					<a href="<?= get_uri('/packages/'); ?>?K=<?= $row['User'] ?>&amp;SeB=m"><?= $row['User'] ?></a>
				<?php else:
					print "N/A";
				endif;
				?>
				</td>
				<td><?= $row['Yes'] ?></td>
				<td><?= $row['No'] ?></td>
				<td>
					<?php if (tu_voted($row['ID'], uid_from_sid($_COOKIE["AURSID"]))): ?>
					<span style="color: green; font-weight: bold"><?= __("Yes") ?></span>
					<?php else: ?>
					<span style="color: red; font-weight: bold"><?= __("No") ?></span>
					<?php endif; ?>
				</td>
			</tr>
			<?php
			endwhile;
			endif;
			?>
		</tbody>
	</table>
</div>
