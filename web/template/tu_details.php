<div class="box">
	<h2><?= __("Proposal Details") ?></h2>

	<?php if ($isrunning == 1): ?>
	<p style="font-weight: bold; color: red">
		<?= __("This vote is still running.") ?>
	</p>
	<?php endif; ?>

	<p>
		<?= __("User") ?>:
		<strong>
			<?php if (!empty($row['User'])): ?>
			<a href="<?= get_uri('/packages/'); ?>?K=<?= $row['User'] ?>&amp;SeB=m"><?= $row['User'] ?></a>
			<?php else: ?>
			N/A
			<?php endif; ?>
		</strong>
		<br />
		<?= __("Submitted: %s by %s", gmdate("Y-m-d H:i", $row['Submitted']), username_from_id($row['SubmitterID'])) ?>
		<br />
		<?= __("End") ?>:
		<strong><?= gmdate("Y-m-d H:i", $row['End']) ?></strong>
	</p>

	<p>
		<?= str_replace("\n", "<br />\n", htmlspecialchars($row['Agenda'])) ?>
	</p>

	<table>
		<tr>
			<th><?= __("Yes") ?></th>
			<th><?= __("No") ?></th>
			<th><?= __("Abstain") ?></th>
			<th><?= __("Total") ?></th>
			<th><?= __('Voted') ?></th>
		</tr>
		<tr>
			<td><?= $row['Yes'] ?></td>
			<td><?= $row['No'] ?></td>
			<td><?= $row['Abstain'] ?></td>
			<td><?= ($row['Yes'] + $row['No'] + $row['Abstain']) ?></td>
			<td>
				<?php if ($hasvoted == 0): ?>
				<span style="color: red; font-weight: bold"><?= __("No") ?></span>
				<?php else: ?>
				<span style="color: green; font-weight: bold"><?= __("Yes") ?></span>
				<?php endif; ?>
			</td>
		</tr>
	</table>
</div>

<?php if (!$isrunning): ?>
<div class="box">
	<h2><?= __("Voters"); ?></h2>
	<ul>
		<?php foreach($whovoted as $voter): ?>
		<li><a href="<?= get_user_uri($voter) ?>"><?= htmlspecialchars($voter) ?></a></li>
		<?php endforeach; ?>
	</ul>
</div>
<?php endif; ?>

<div class="box">

<?php if ($canvote == 1): ?>
	<form action="<?= get_uri('/tu/'); ?>?id=<?= $row['ID'] ?>" method="post">
		<fieldset>
			<input type="submit" class="button" name="voteYes" value="<?= __("Yes") ?>" />
			<input type="submit" class="button" name="voteNo" value="<?= __("No") ?>" />
			<input type="submit" class="button" name="voteAbstain" value="<?= __("Abstain") ?>" />
			<input type="hidden" name="doVote" value="1" />
			<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
		</fieldset>
	</form>
<?php else:
	print $errorvote ?>
<?php endif; ?>
</div>
