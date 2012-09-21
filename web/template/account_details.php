<table>
	<tr>
		<td colspan="2">&nbsp;</td>
	</tr>

	<tr>
		<td align="left"><?= __("Username") . ":" ?></td>
		<td align="left"><?= $row["Username"] ?></td>
	</tr>

	<tr>
		<td align="left"><?= __("Account Type") . ":" ?></td>
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
		<td align="left"><?= __("Email Address") . ":" ?></td>
		<td align="left"><a href="mailto:<?= htmlspecialchars($row["Email"], ENT_QUOTES) ?>"><?= htmlspecialchars($row["Email"], ENT_QUOTES) ?></a></td>
	</tr>

	<tr>
		<td align="left"><?= __("Real Name") . ":" ?></td>
		<td align="left"><?= htmlspecialchars($row["RealName"], ENT_QUOTES) ?></td>
	</tr>

	<tr>
		<td align="left"><?= __("IRC Nick") . ":" ?></td>
		<td align="left"><?= htmlspecialchars($row["IRCNick"], ENT_QUOTES) ?></td>
	</tr>

	<tr>
		<td align="left"><?= __("PGP Key Fingerprint") . ":" ?></td>
		<td align="left"><?= html_format_pgp_fingerprint($row["PGPKey"]) ?></td>
	</tr>

	<tr>
		<td align="left"><?= __("Last Voted") . ":" ?></td>
		<td align="left">
		<?= $row["LastVoted"] ? date("Y-m-d", $row["LastVoted"]) : __("Never"); ?>
		</td>
	</tr>

	<tr>
		<td colspan="2"><a href="<?= get_uri('/packages/'); ?>?K=<?= $row['Username'] ?>&amp;SeB=m"><?= __("View this user's packages") ?></a></td>
	</tr>

</table>
