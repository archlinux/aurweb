<div class="pgbox">
	<h2><?php print $type ?></h2>
			<table class='results'>
				<tr>
					<th class='header'><span class='f2'><?php print __("Proposal") ?></span></th>
					<th class='header'><span class='f2'>
						<a href='?off=<?php print $off ?>&amp;by=<?php print $by_next ?>'><?php print __("Start") ?></a>
					</span></th>
					<th class='header'><span class='f2'><?php print __("End") ?></span></th>
					<th class='header'><span class='f2'><?php print __("User") ?></span></th>
					<th class='header'><span class='f2'><?php print __("Yes") ?></span></th>
					<th class='header'><span class='f2'><?php print __("No") ?></span></th>
					<th class='header'><span class='f2'><?php print __('Voted') ?></span></th>
				</tr>
				<?php if (mysql_num_rows($result) == 0) { ?>
				<tr><td align='center' colspan='0'><?php print __("No results found.") ?></td></tr>
				<?php } else { for ($i = 0; $row = mysql_fetch_assoc($result); $i++) { (($i % 2) == 0) ? $c = "data1" : $c = "data2"; ?>
				<tr>
					<td class='<?php print $c ?>'><span class='f4'><span class='blue'>
						<?php
							$row["Agenda"] = htmlspecialchars(substr($row["Agenda"], 0, $prev_Len));
						?>
						<a href='tu.php?id=<?php print $row['ID'] ?>'><?php print $row["Agenda"] ?></a></span></span>
					</td>
					<td class='<?php print $c ?>'><span class='f5'><span class='blue'><?php print gmdate("Y-m-d", $row["Submitted"]) ?></span></span></td>
					<td class='<?php print $c ?>'><span class='f5'><span class='blue'><?php print gmdate("Y-m-d", $row["End"]) ?></span></span></td>
					<td class='<?php print $c ?>'><span class='f6'><span class='blue'>
					<?php
					if (!empty($row['User'])) {
						print "<a href='packages.php?K=" . $row['User'] . "&amp;SeB=m'>" . $row['User'] . "</a>";
					} else {
						print "N/A";
					}
					?>
					</span></span></td>
					<td class='<?php print $c ?>'><span class='f5'><span class='blue'><?php print $row['Yes'] ?></span></span></td>
					<td class='<?php print $c ?>'><span class='f5'><span class='blue'><?php print $row['No'] ?></span></span></td>
					<td class='<?php print $c ?>'>
						<?php
						$q = "SELECT * FROM TU_Votes WHERE VoteID = " . $row['ID'] . " AND UserID = " . uid_from_sid($_COOKIE["AURSID"]);
						$result_tulist = db_query($q, $dbh);
						if ($result_tulist) {
							$hasvoted = mysql_num_rows($result_tulist);
						}
						else {
							$hasvoted = 0;
						}
						?>
						<span class='f5'><span class='blue'>
						<?php if ($hasvoted == 0) { ?>
						<span style='color: red; font-weight: bold'><?php print __("No") ?></span>
						<?php } else { ?>
						<span style='color: green; font-weight: bold'><?php print __("Yes") ?></span>
						<?php } ?>
						</span></span>
					</td>
				</tr>
				<?php } } ?>
			</table>
</div>
