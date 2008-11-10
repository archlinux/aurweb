<center>
<table cellspacing='3' class='boxSoft'>
	<tr>
		<td class='boxSoftTitle' align='right'>
			<span class='f3'><?php print $type ?></span>
		</td>
	</tr>
	<tr>
		<td class='boxSoft'>
			<table width='100%' cellspacing='0' cellpadding='2'>
				<tr>
					<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'><?php print __("Proposal") ?></span></th>
					<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'>
						<a href='?off=<?php print $off ?>&amp;by=<?php print $by_next ?>'><?php print __("Start") ?></a>
					</span></th>
					<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'><?php print __("End") ?></span></th>
					<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'><?php print __("User") ?></span></th>
					<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'><?php print __("Yes") ?></span></th>
					<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'><?php print __("No") ?></span></th>
					<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'><?php print __("Voted?") ?></span></th>
				</tr>
				<?php if (mysql_num_rows($result) == 0) { ?>
				<tr><td align='center' colspan='0'><?php print __("No results found.") ?></td></tr>
				<?php } else { for ($i = 0; $row = mysql_fetch_assoc($result); $i++) { (($i % 2) == 0) ? $c = "data1" : $c = "data2"; ?>
				<tr>
					<td class='<?php print $c ?>'><span class='f4'><span class='blue'>
						<?php
						if (strlen($row["Agenda"]) >= $prev_Len) {
							$row["Agenda"] = htmlentities(substr($row["Agenda"], 0, $prev_Len)) . "...";
						} else {
							$row["Agenda"] = htmlentities($row["Agenda"]);
						}
						?>
						<a href='tu.php?id=<?php print $row['ID'] ?>'><?php print $row["Agenda"] ?></a></span></span>
					</td>
					<td class='<?php print $c ?>'><span class='f5'><span class='blue'><?php print gmdate("j M y", $row["Submitted"]) ?></span></span></td>
					<td class='<?php print $c ?>'><span class='f5'><span class='blue'><?php print gmdate("j M y", $row["End"]) ?></span></span></td>
					<td class='<?php print $c ?>'><span class='f6'><span class='blue'>
					<?php
					if (!empty($row['User'])) {
						print "<a href='packages.php?K=" . $row['User'] . "&SeB=m'>" . $row['User'] . "</a>";
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
						$hasvoted = mysql_num_rows(db_query($q, $dbh));
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
		</td>
	</tr>
</table>
</center>
