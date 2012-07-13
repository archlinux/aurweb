<?php
$username = username_from_sid($_COOKIE["AURSID"]);
?>

<h3><?php echo __("My Statistics"); ?></h3>

<table>
	<tr>
		<td>
			<a href="<?php echo get_uri('/packages/'); ?>?SeB=m&amp;L=2&amp;K=<?php echo $username; ?>">
<?php print __("Packages in unsupported"); ?></a>
		</td>
		<td><?php print $maintainer_unsupported_count; ?></td>
	</tr>
	<tr>
		<td>
			<a href="<?php echo get_uri('/packages/'); ?>?SeB=m&amp;outdated=on&amp;K=<?php echo $username; ?>"><?php print __("Out of Date"); ?></a>
		</td>
		<td><?php echo $flagged_outdated ?></td>
	</tr>
</table>
