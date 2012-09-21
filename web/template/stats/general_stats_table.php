<h3><?= __("Statistics") ?></h3>

<table>
	<tr>
		<td><?= __("Packages"); ?></td>
		<td><?= $unsupported_count; ?></td>
	</tr>
	<tr>
		<td><?= __("Orphan Packages"); ?></td>
		<td><?= $orphan_count; ?></td>
	</tr>
	<tr>
		<td><?= __("Packages added in the past 7 days"); ?></td>
		<td><?= $add_count; ?></td>
	</tr>
	<tr>
		<td><?= __("Packages updated in the past 7 days"); ?></td>
		<td><?= $update_count; ?></td>
	</tr>
	<tr>
		<td><?= __("Packages updated in the past year"); ?></td>
		<td><?= $update_year_count; ?></td>
	</tr>
	<tr>
		<td><?= __("Packages never updated"); ?></td>
		<td><?= $never_update_count; ?></td>
	</tr>
	<tr>
		<td><?= __("Registered Users"); ?></td>
		<td><?= $user_count; ?></td>
	</tr>
	<tr>
		<td><?= __("Trusted Users"); ?></td>
		<td><?= $tu_count; ?></td>
	</tr>
</table>
