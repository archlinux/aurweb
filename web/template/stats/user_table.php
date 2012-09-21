<?php
$username = username_from_sid($_COOKIE["AURSID"]);
?>

<h3><?= __("My Statistics"); ?></h3>

<table>
	<tr>
		<td>
			<a href="<?= get_uri('/packages/'); ?>?SeB=m&amp;L=2&amp;K=<?= $username; ?>">
<?= __("Packages in unsupported"); ?></a>
		</td>
		<td><?= $maintainer_unsupported_count; ?></td>
	</tr>
	<tr>
		<td>
			<a href="<?= get_uri('/packages/'); ?>?SeB=m&amp;outdated=on&amp;K=<?= $username; ?>"><?= __("Out of Date"); ?></a>
		</td>
		<td><?= $flagged_outdated ?></td>
	</tr>
</table>
