<h3><?= __("Statistics") ?></h3>

<table>
	<tr>
		<td class="stat-desc"><?= __("Packages"); ?></td>
		<td><?= $pkg_count; ?></td>
	</tr>
	<tr>
		<td class="stat-desc"><?= __("Orphan Packages"); ?></td>
		<td><?= $orphan_count; ?></td>
	</tr>
	<tr>
		<td class="stat-desc"><?= __("Packages added in the past 7 days"); ?></td>
		<td><?= $add_count; ?></td>
	</tr>
	<tr>
		<td class="stat-desc"><?= __("Packages updated in the past 7 days"); ?></td>
		<td><?= $update_count; ?></td>
	</tr>
	<tr>
		<td class="stat-desc"><?= __("Packages updated in the past year"); ?></td>
		<td><?= $update_year_count; ?></td>
	</tr>
	<tr>
		<td class="stat-desc"><?= __("Packages never updated"); ?></td>
		<td><?= $never_update_count; ?></td>
	</tr>
	<tr>
		<td class="stat-desc"><?= __("Registered Users"); ?></td>
		<td><?= $user_count; ?></td>
	</tr>
	<tr>
		<td class="stat-desc"><?= __("Trusted Users"); ?></td>
		<td><?= $tu_count; ?></td>
	</tr>
</table>
