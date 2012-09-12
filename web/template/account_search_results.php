<?php
if (!$result):
	print __("No results matched your search criteria.");
else:
	if ($result):
?>
		<table class="results">
			<thead>
				<tr>
					<th><?php echo __("Username") ?></th>
					<th><?php echo __("Type") ?></th>
					<th><?php echo __("Status") ?></th>
					<th><?php echo __("Real Name") ?></th>
					<th><?php echo __("IRC Nick") ?></th>
					<th><?php echo __("PGP Key Fingerprint") ?></th>
					<th><?php echo __("Last Voted") ?></th>
					<th><?php echo __("Edit Account") ?></th>
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
				<tr class ="<?php echo $c ?>">
					<td><a href="<?php echo get_uri('/packages/'); ?>?SeB=m&amp;K=<?php echo $row["Username"] ?>"><?php echo $row["Username"] ?></a></td>
					<td><?php echo $row["AccountType"] ?></td>
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
					<td><?php $row["LastVoted"] ? print date("Y-m-d", $row["LastVoted"]) : print __("Never") ?></td>
					<td>
					<?php
						if ($UTYPE == "Trusted User" && $row["AccountType"] == "Developer"):
							# TUs can't edit devs
							print "&nbsp;";
						else:
					?>
						<a href="<?php echo get_user_uri($row["Username"]) . "edit/" ?>"><?php echo __("Edit") ?></a>
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
			<form action="<?php echo get_uri('/accounts/'); ?>" method="post">
					<fieldset>
						<input type="hidden" name="Action" value="SearchAccounts" />
						<input type="hidden" name="O" value="<?php echo ($OFFSET-$HITS_PER_PAGE) ?>" />
						<?php
						reset($search_vars);
						while (list($k, $ind) = each($search_vars)):
						?>
						<input type="hidden" name="<?php echo $ind ?>" value="<?php echo ${$ind} ?>" />
						<?php endwhile; ?>
						<input type="submit" class="button" value="&lt;-- <?php echo __("Less") ?>" />
					</fieldset>
				</form>
			</td>
			<td align="right">
				<form action="<?php echo get_uri('/accounts/'); ?>" method="post">
					<fieldset>
						<input type="hidden" name="Action" value="SearchAccounts" />
						<input type="hidden" name="O" value="<?php echo ($OFFSET+$HITS_PER_PAGE) ?>" />
						<?php
						reset($search_vars);
						while (list($k, $ind) = each($search_vars)):
						?>
						<input type="hidden" name="<?php echo $ind ?>" value="<?php echo ${$ind} ?>" />
						<?php endwhile; ?>
						<input type="submit" class="button" value="<?php echo __("More") ?> --&gt;" />
					</fieldset>
				</form>
			</td>
		</tr>
	</table>
	<?php else: ?>
		<p style="text-align:center;">
			<?php print __("No more results to display."); ?>
		</p>
	<?php endif; ?>
<?php endif; ?>
