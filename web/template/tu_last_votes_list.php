<div class="box">
	<h2><?= __("Last Votes by TU") ?></h2>
	<table class="results">
		<thead>
			<tr>
				<th><?= __("User") ?></th>
				<th><?= __("Last vote") ?></th>
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
				$username = username_from_id($row["UserID"]);
			?>
			<tr class="<?= $c ?>">
				<td>
					<?php if (!use_virtual_urls()): ?>
					<a href="<?= get_uri('/account/'); ?>?Action=AccountInfo&amp;ID=<?= htmlspecialchars($row['UserID'], ENT_QUOTES) ?>" title="<?= __('View account information for')?> <?= html_format_username($username) ?>"><?= html_format_username($username) ?></a></td>
					<?php else: ?>
					<a href="<?= get_uri('/account/') . html_format_username($username) ?>" title="<?= __('View account information for %s', html_format_username($username)) ?>"><?= html_format_username($username) ?></a>
					<?php endif; ?>
				</td>
				<td>
					<a href="<?= get_uri('/tu/'); ?>?id=<?= $row['LastVote'] ?>"><?= intval($row["LastVote"]) ?></a>
				</td>
			</tr>
			<?php
			endwhile;
			endif;
			?>
		</tbody>
	</table>
</div>
