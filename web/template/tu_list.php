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
			<?php if (mysql_num_rows($result) == 0): ?>
			<tr><td align="center" colspan="0"><?php print __("No results found.") ?></td></tr>
			<?php else: for ($i = 0; $row = mysql_fetch_assoc($result); $i++): (($i % 2) == 0) ? $c = 'odd' : $c = 'even'; ?>
			<tr class="<?php print $c ?>">
				<td><?php $row["Agenda"] = htmlspecialchars(substr($row["Agenda"], 0, $prev_Len)); ?>
					<a href="tu.php?id=<?php print $row['ID'] ?>"><?php print $row["Agenda"] ?></a></span></span>
				</td>
				<td><?php print gmdate("Y-m-d", $row["Submitted"]) ?></td>
				<td><?php print gmdate("Y-m-d", $row["End"]) ?></td>
				<td>
				<?php if (!empty($row['User'])): ?>
					<a href="packages.php?K=<?php echo $row['User'] ?>&amp;SeB=m"><?php echo $row['User'] ?></a>
				<?php else:
					print "N/A";
				endif;
				?>
				</td>
				<td><?php print $row['Yes'] ?></td>
				<td><?php print $row['No'] ?></td>
				<td>
					<?php
					$q = "SELECT * FROM TU_Votes WHERE VoteID = " . $row['ID'] . " AND UserID = " . uid_from_sid($_COOKIE["AURSID"]);
					$result_tulist = db_query($q, $dbh);
					if ($result_tulist):
						$hasvoted = mysql_num_rows($result_tulist);
					else:
						$hasvoted = 0;
					endif;
						if ($hasvoted == 0): ?>
					<span style="color: red; font-weight: bold"><?php print __("No") ?></span>
					<?php else: ?>
					<span style="color: green; font-weight: bold"><?php print __("Yes") ?></span>
					<?php endif; ?>
				</td>
			</tr>
			<?php
			endfor;
			endif;
			?>
		</tbody>
	</table>
</div>
