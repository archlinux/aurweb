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
					<?php if (!$USE_VIRTUAL_URLS): ?>
					<a href="<?= get_uri('/account/'); ?>?Action=AccountInfo&amp;ID=<?= htmlspecialchars($row['UserID'], ENT_QUOTES) ?>" title="<?= __('View account information for')?> <?= htmlspecialchars($username) ?>"><?= htmlspecialchars($username) ?></a></td>
					<?php else: ?>
					<a href="<?= get_uri('/account/') . htmlspecialchars($username, ENT_QUOTES) ?>" title="<?= __('View account information for %s', htmlspecialchars($username)) ?>"><?= htmlspecialchars($username) ?></a>
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
