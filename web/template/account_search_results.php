<?php
if (!$result):
	print __("No results matched your search criteria.");
else:
	if ($result):
?>
		<table class="results">
			<thead>
				<tr>
					<th><?= __("Username") ?></th>
					<th><?= __("Type") ?></th>
					<th><?= __("Status") ?></th>
					<th><?= __("Real Name") ?></th>
					<th><?= __("IRC Nick") ?></th>
					<th><?= __("PGP Key Fingerprint") ?></th>
					<th><?= __("Edit Account") ?></th>
				</tr>
			</thead>
			<?php
			$i = 0;
			while (list($indx, $row) = each($userinfo)):
				if ($i % 2):
					$c = "even";
				else:
					$c = "odd";
				endif;
			?>
				<tbody>
				<tr class ="<?= $c ?>">
					<td><a href="<?= get_uri('/packages/'); ?>?SeB=m&amp;K=<?= $row["Username"] ?>"><?= $row["Username"] ?></a></td>
					<td><?= $row["AccountType"] ?></td>
					<td>
						<?php
						if ($row["Suspended"]):
							print __("Suspended");
						else:
							print __("Active");
						endif;
						?>
					</td>
					<td><?php $row["RealName"] ? print htmlspecialchars($row["RealName"],ENT_QUOTES) : print "&nbsp;" ?></td>
					<td><?php $row["IRCNick"] ? print htmlspecialchars($row["IRCNick"],ENT_QUOTES) : print "&nbsp;" ?></td>
					<td><?php $row["PGPKey"] ? print html_format_pgp_fingerprint($row["PGPKey"]) : print "&nbsp;" ?></td>
					<td>
					<?php if (can_edit_account($row)): ?>
					<a href="<?= get_user_uri($row["Username"]) . "edit/" ?>"><?= __("Edit") ?></a>
					<?php else: ?>
					&nbsp;
					<?php endif; ?>
					</td>
				</tr>
			<?php
				$i++;
			endwhile;
			?>
	</table>

	<table class="results">
		<tr>
			<td align="left">
			<form action="<?= get_uri('/accounts/'); ?>" method="post">
					<fieldset>
						<input type="hidden" name="Action" value="SearchAccounts" />
						<input type="hidden" name="O" value="<?= ($OFFSET-$HITS_PER_PAGE) ?>" />
						<?php
						reset($search_vars);
						while (list($k, $ind) = each($search_vars)):
						?>
						<input type="hidden" name="<?= $ind ?>" value="<?= ${$ind} ?>" />
						<?php endwhile; ?>
						<input type="submit" class="button" value="&lt;-- <?= __("Less") ?>" />
					</fieldset>
				</form>
			</td>
			<td align="right">
				<form action="<?= get_uri('/accounts/'); ?>" method="post">
					<fieldset>
						<input type="hidden" name="Action" value="SearchAccounts" />
						<input type="hidden" name="O" value="<?= ($OFFSET+$HITS_PER_PAGE) ?>" />
						<?php
						reset($search_vars);
						while (list($k, $ind) = each($search_vars)):
						?>
						<input type="hidden" name="<?= $ind ?>" value="<?= ${$ind} ?>" />
						<?php endwhile; ?>
						<input type="submit" class="button" value="<?= __("More") ?> --&gt;" />
					</fieldset>
				</form>
			</td>
		</tr>
	</table>
	<?php else: ?>
		<p style="text-align:center;">
			<?= __("No more results to display."); ?>
		</p>
	<?php endif; ?>
<?php endif; ?>
