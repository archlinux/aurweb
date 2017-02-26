<?php
$yes = $row["Yes"];
$no = $row["No"];
$abstain = $row["Abstain"];
$active_tus = $row["ActiveTUs"];
$quorum = $row["Quorum"];

$total = $yes + $no + $abstain;
if ($active_tus > 0) {
	$participation = $total / $active_tus;
} else {
	$participation = 0;
}

if ($yes > $active_tus / 2) {
	$vote_accepted = true;
} elseif ($participation > $quorum && $yes > $no) {
	$vote_accepted = true;
} else {
	$vote_accepted = false;
}
?>
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
		<?= __("Submitted: %s by %s", date("Y-m-d H:i", $row['Submitted']), html_format_username(username_from_id($row['SubmitterID']))) ?>
		<br />
		<?= __("End") ?>:
		<strong><?= date("Y-m-d H:i", $row['End']) ?></strong>
		<?php if ($isrunning == 0): ?>
		<br />
		<?= __("Result") ?>:
		<?php if ($active_tus == 0): ?>
		<span><?= __("unknown") ?></span>
		<?php elseif ($vote_accepted): ?>
		<span style="color: green; font-weight: bold"><?= __("Accepted") ?></span>
		<?php else: ?>
		<span style="color: red; font-weight: bold"><?= __("Rejected") ?></span>
		<?php endif; ?>
		<?php endif; ?>
	</p>

	<p>
		<?= str_replace("\n", "<br />\n", htmlspecialchars($row['Agenda'])) ?>
	</p>

	<table>
		<tr>
			<?php if (!$isrunning): ?>
			<th><?= __("Yes") ?></th>
			<th><?= __("No") ?></th>
			<th><?= __("Abstain") ?></th>
			<?php endif; ?>
			<th><?= __("Total") ?></th>
			<th><?= __('Voted') ?></th>
			<th><?= __('Participation') ?></th>
		</tr>
		<tr>
			<?php if (!$isrunning): ?>
			<td><?= $yes ?></td>
			<td><?= $no ?></td>
			<td><?= $abstain ?></td>
			<?php endif; ?>
			<td><?= $total ?></td>
			<td>
				<?php if ($hasvoted == 0): ?>
				<span style="color: red; font-weight: bold"><?= __("No") ?></span>
				<?php else: ?>
				<span style="color: green; font-weight: bold"><?= __("Yes") ?></span>
				<?php endif; ?>
			</td>
			<?php if ($active_tus > 0): ?>
			<td><?= number_format($participation * 100, 2) ?>%</td>
			<?php else: ?>
			<td><?= __("unknown") ?></td>
			<?php endif; ?>
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
