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
			<?php else: foreach ($result as $indx => $row):
				if ($indx % 2):
					$c = "even";
				else:
					$c = "odd";
				endif;
				$username = username_from_id($row["UserID"]);
			?>
			<tr class="<?= $c ?>">
				<td>
					<?= html_format_username($username) ?>
				</td>
				<td>
					<a href="<?= get_uri('/tu/'); ?>?id=<?= $row['LastVote'] ?>"><?= intval($row["LastVote"]) ?></a>
				</td>
			</tr>
			<?php
			endforeach;
			endif;
			?>
		</tbody>
	</table>
</div>
