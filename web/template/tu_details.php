<div class="box">
	<h2><?php print __("Proposal Details") ?></h2>

	<?php if ($isrunning == 1): ?>
	<p style="font-weight: bold; color: red">
		<?php print __("This vote is still running.") ?>
	</p>
	<?php endif; ?>

	<p>
		<?php echo __("User") ?>:
		<b>
			<?php if (!empty($row['User'])): ?>
			<a href="packages.php?K=<?php print $row['User'] ?>&amp;SeB=m"><?php print $row['User'] ?></a>
			<?php else: ?>
			N/A
			<?php endif; ?>
		</b>
		<br />
		<?php print __("Submitted: %s by %s", "<b>" . gmdate("Y-m-d H:i", $row['Submitted']) . "</b>", "<b>" . username_from_id($row['SubmitterID']) . "</b>") ?>
		<br />
		<?php print __("End") ?>:
		<b><?php print gmdate("Y-m-d H:i", $row['End']) ?></b>
	</p>

	<p>
		<?php print str_replace("\n", "<br />\n", htmlspecialchars($row['Agenda'])) ?>
	</p>

	<table>
		<tr>
			<th><?php print __("Yes") ?></th>
			<th><?php print __("No") ?></th>
			<th><?php print __("Abstain") ?></th>
			<th><?php print __("Total") ?></th>
			<th><?php print __('Voted') ?></th>
		</tr>
		<tr>
			<td><?php print $row['Yes'] ?></td>
			<td><?php print $row['No'] ?></td>
			<td><?php print $row['Abstain'] ?></td>
			<td><?php print ($row['Yes'] + $row['No'] + $row['Abstain']) ?></td>
			<td>
				<?php if ($hasvoted == 0): ?>
				<span style="color: red; font-weight: bold"><?php print __("No") ?></span>
				<?php else: ?>
				<span style="color: green; font-weight: bold"><?php print __("Yes") ?></span>
				<?php endif; ?>
			</td>
		</tr>
	</table>
</div>

<?php if (!$isrunning): ?>
<div class="box">
	<h2><?php echo __("Voters"); ?></h2>
	<?php echo $whovoted; ?>
</div>
<?php endif; ?>

<div class="box">

<?php if ($canvote == 1): ?>
	<form action="tu.php?id=<?php print $row['ID'] ?>" method="post">
		<fieldset>
			<input type="submit" class="button" name="voteYes" value="<?php print __("Yes") ?>" />
			<input type="submit" class="button" name="voteNo" value="<?php print __("No") ?>" />
			<input type="submit" class="button" name="voteAbstain" value="<?php print __("Abstain") ?>" />
			<input type="hidden" name="doVote" value="1" />
		</fieldset>
	</form>
<?php else:
	print $errorvote ?>
<?php endif; ?>
</div>
