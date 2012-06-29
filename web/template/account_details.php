<table>
	<tr>
		<td colspan="2">&nbsp;</td>
	</tr>

	<tr>
		<td align="left"><?php echo __("Username") . ":" ?></td>
		<td align="left"><?php echo $row["Username"] ?></td>
	</tr>

	<tr>
		<td align="left"><?php echo __("Account Type") . ":" ?></td>
		<td align="left">
			<?php
			if ($row["AccountType"] == "User") {
				print __("User");
			} elseif ($row["AccountType"] == "Trusted User") {
				print __("Trusted User");
			} elseif ($row["AccountType"] == "Developer") {
				print __("Developer");
			}
			?>
		</td>
	</tr>

	<tr>
		<td align="left"><?php echo __("Email Address") . ":" ?></td>
		<td align="left"><a href="mailto:<?php echo htmlspecialchars($row["Email"], ENT_QUOTES) ?>"><?php echo htmlspecialchars($row["Email"], ENT_QUOTES) ?></a></td>
	</tr>

	<tr>
		<td align="left"><?php echo __("Real Name") . ":" ?></td>
		<td align="left"><?php echo htmlspecialchars($row["RealName"], ENT_QUOTES) ?></td>
	</tr>

	<tr>
		<td align="left"><?php echo __("IRC Nick") . ":" ?></td>
		<td align="left"><?php echo htmlspecialchars($row["IRCNick"], ENT_QUOTES) ?></td>
	</tr>

	<tr>
		<td align="left"><?php echo __("PGP Key Fingerprint") . ":" ?></td>
		<td align="left"><?php echo html_format_pgp_fingerprint($row["PGPKey"]) ?></td>
	</tr>

	<tr>
		<td align="left"><?php echo __("Last Voted") . ":" ?></td>
		<td align="left">
		<?php print $row["LastVoted"] ? date("Y-m-d", $row["LastVoted"]) : __("Never"); ?>
		</td>
	</tr>

	<tr>
		<td colspan="2"><a href="packages.php?K=<?php echo $row['Username'] ?>&amp;SeB=m"><?php echo __("View this user's packages") ?></a></td>
	</tr>

</table>
