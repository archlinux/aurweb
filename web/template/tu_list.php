<div class="box">
	<h2><?php print $type ?></h2>
	<table class="results">
		<thead>
			<tr>
				<th><?php print __("Proposal") ?></th>
				<th><a href="?off=<?php print $off ?>&amp;by=<?php print $by_next ?>"><?php print __("Start") ?></a></th>
				<th><?php print __("End") ?></th>
				<th><?php print __("User") ?></th>
				<th><?php print __("Yes") ?></th>
				<th><?php print __("No") ?></th>
				<th><?php print __('Voted') ?></th>
			</tr>
		</thead>

		<tbody>
			<?php if (empty($result)): ?>
			<tr><td align="center" colspan="0"><?php print __("No results found.") ?></td></tr>
			<?php else: while (list($indx, $row) = each($result)):
				if ($indx % 2):
					$c = "even";
				else:
					$c = "odd";
				endif;
			?>
			<tr class="<?php print $c ?>">
				<td><?php $row["Agenda"] = htmlspecialchars(substr($row["Agenda"], 0, $prev_Len)); ?>
					<a href="<?php echo get_uri('/tu/'); ?>?id=<?php print $row['ID'] ?>"><?php print $row["Agenda"] ?></a></span></span>
				</td>
				<td><?php print gmdate("Y-m-d", $row["Submitted"]) ?></td>
				<td><?php print gmdate("Y-m-d", $row["End"]) ?></td>
				<td>
				<?php if (!empty($row['User'])): ?>
					<a href="<?php echo get_uri('/packages/'); ?>?K=<?php echo $row['User'] ?>&amp;SeB=m"><?php echo $row['User'] ?></a>
				<?php else:
					print "N/A";
				endif;
				?>
				</td>
				<td><?php print $row['Yes'] ?></td>
				<td><?php print $row['No'] ?></td>
				<td>
					<?php if (tu_voted($row['ID'], uid_from_sid($_COOKIE["AURSID"]))): ?>
					<span style="color: green; font-weight: bold"><?php print __("Yes") ?></span>
					<?php else: ?>
					<span style="color: red; font-weight: bold"><?php print __("No") ?></span>
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
