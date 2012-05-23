<h3><?php echo __("Statistics") ?></h3>

<table>
	<tr>
		<td><?php print __("Packages"); ?></td>
		<td><?php print $unsupported_count; ?></td>
	</tr>
	<tr>
		<td><?php print __("Orphan Packages"); ?></td>
		<td><?php print $orphan_count; ?></td>
	</tr>
	<tr>
		<td><?php print __("Packages added in the past 7 days"); ?></td>
		<td><?php print $add_count; ?></td>
	</tr>
	<tr>
		<td><?php print __("Packages updated in the past 7 days"); ?></td>
		<td><?php print $update_count; ?></td>
	</tr>
	<tr>
		<td><?php print __("Packages updated in the past year"); ?></td>
		<td><?php print $update_year_count; ?></td>
	</tr>
	<tr>
		<td><?php print __("Packages never updated"); ?></td>
		<td><?php print $never_update_count; ?></td>
	</tr>
	<tr>
		<td><?php print __("Registered Users"); ?></td>
		<td><?php print $user_count; ?></td>
	</tr>
	<tr>
		<td><?php print __("Trusted Users"); ?></td>
		<td><?php print $tu_count; ?></td>
	</tr>
</table>
