<?php if (!$result) { ?>
	<div class='pgboxbody'><?php print __("Error retrieving package list.") ?></div>
<?php } elseif ($total == 0) { ?>
	<div class='pgboxbody'><?php print __("No packages matched your search criteria.") ?></div>
<?php } else { ?>
	<form action='packages.php?<?php echo htmlentities($_SERVER['QUERY_STRING']) ?>' method='post'>
		<div class="pgbox">
			<div class="pgboxtitle">
				<span class='f3'><?php print __("Package Listing") ?></span>
			</div>




<table width='100%' cellspacing='0' cellpadding='2'>
<tr>
	<?php if ($SID): ?>
	<th style='border-bottom: #666 1px solid; vertical-align: bottom'>&nbsp;</th>
	<?php endif; ?>

	<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'>
		<a href='?<?php print mkurl('SB=c&SO=' . $SO_next) ?>'><?php print __("Category") ?></a>
	</span></th>
	<th style='border-bottom: #666 1px solid; vertical-align: bottom; text-align: center;'><span class='f2'>
		<a href='?<?php print mkurl('SB=n&SO=' . $SO_next) ?>'><?php print __("Name") ?></a>
	</span></th>
	<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'>
		<a href='?<?php print mkurl('SB=v&SO=' . $SO_next) ?>'><?php print __("Votes") ?></a>
	</span></th>

	<?php if ($SID): ?>
	<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'>
		<a href='?<?php print mkurl('SB=w&SO=' . $SO_next) ?>'><?php print __("Voted") ?></a>
	</span></th>
	<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'>
		<a href='?<?php print mkurl('SB=o&SO=' . $SO_next) ?>'><?php print __("Notify") ?></a>
	</span></th>
	<?php endif; ?>
	<th style='border-bottom: #666 1px solid; vertical-align: bottom; text-align: center;'><span class='f2'><?php print __("Description") ?></span></th>
	<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'>
		<a href='?<?php print mkurl('SB=m&SO=' . $SO_next) ?>'><?php print __("Maintainer") ?></a>
	</span></th>
</tr>

<?php
if (isset($_COOKIE['AURSID'])) {
	$atype = account_from_sid($_COOKIE['AURSID']);
} else {
	$atype = "";
}
for ($i = 0; $row = mysql_fetch_assoc($result); $i++) {
	(($i % 2) == 0) ? $c = "data1" : $c = "data2";
	if ($row["OutOfDateTS"] !== NULL): $c = "outofdate"; endif;
?>
<tr>
	<?php if ($SID): ?>
	<td class='<?php print $c ?>'><input type='checkbox' name='IDs[<?php print $row["ID"] ?>]' value='1' /></td>
	<?php endif; ?>
	<td class='<?php print $c ?>'><span class='f5'><span class='blue'><?php print htmlspecialchars($row["Category"]) ?></span></span></td>
	<td class='<?php print $c ?>'><span class='f4'><a href='packages.php?ID=<?php print $row["ID"] ?>'><span class='black'><?php print htmlspecialchars($row["Name"]) ?> <?php print htmlspecialchars($row["Version"]) ?></span></a></span></td>
	<td class='<?php print $c ?>' style="text-align: right"><span class='f5'><span class='blue'><?php print $row["NumVotes"] ?></span></span></td>
	<?php if ($SID): ?>
	<td class='<?php print $c ?>'><span class='f5'><span class='blue'>
	<?php if (isset($row["Voted"])): ?>
	<?php print __("Yes") ?></span></span></td>
	<?php else: ?>
	</span></span></td>
	<?php endif; ?>
	<td class='<?php print $c ?>'><span class='f5'><span class='blue'>
	<?php if (isset($row["Notify"])): ?>
	<?php print __("Yes") ?></span></span></td>
	<?php else: ?>
	</span></span></td>
	<?php endif; ?>
	<?php endif; ?>
	<td class='<?php print $c ?>'><span class='f4'><span class='blue'>
	<?php print htmlspecialchars($row['Description'], ENT_QUOTES); ?></span></span></td>
	<td class='<?php print $c ?>'><span class='f5'><span class='blue'>
	<?php if (isset($row["Maintainer"])): ?>
	<a href='packages.php?K=<?php print htmlspecialchars($row['Maintainer'], ENT_QUOTES) ?>&amp;SeB=m'><?php print htmlspecialchars($row['Maintainer']) ?></a>
	<?php else: ?>
	<span style='color: blue; font-style: italic;'><?php print __("orphan") ?></span>
	<?php endif; ?>
	</span></span></td>
</tr>
<?php } ?>

	</table>
</div> <!-- .pgbox ??! -->


		<div class="pgbox pkg_search_results_footer">
			<div class="legend_and_actions">
				<div class="legend">
					<span class='f3'><?php echo __('Legend') ?></span>
					<span class="outofdate"><?php print __('Out of Date') ?></span>
				</div>
				<?php if ($SID): ?>
					<div>
						<select name='action'>
							<option><?php print __("Actions") ?></option>
							<option value='do_Flag'><?php print __("Flag Out-of-date") ?></option>
							<option value='do_UnFlag'><?php print __("Unflag Out-of-date") ?></option>
							<option value='do_Adopt'><?php print __("Adopt Packages") ?></option>
							<option value='do_Disown'><?php print __("Disown Packages") ?></option>
							<?php if ($atype == "Trusted User" || $atype == "Developer"): ?>
							<option value='do_Delete'><?php print __("Delete Packages") ?></option>
							<?php endif; ?>
							<option value='do_Notify'><?php print __("Notify") ?></option>
							<option value='do_UnNotify'><?php print __("UnNotify") ?></option>
						</select>
						<?php if ($atype == "Trusted User" || $atype == "Developer"): ?>
							<label for='merge_Into'><?php print __("Merge into") ?></label>
							<input type='text' id='merge_Into' name='merge_Into' />
							<input type='checkbox' name='confirm_Delete' value='1' /> <?php print __("Confirm") ?>
						<?php endif; ?>
						<input type='submit' class='button' style='width: 80px' value='<?php print __("Go") ?>' />
					</div>
				<?php endif; # if ($SID) ?>
			</div> <!-- .legend_and_actions -->
			<div class="page_links">
				<div class="f4 blue">
					<?php print __("Showing results %s - %s of %s", $first, $last, $total) ?>
				</div>
				<div class="page_nav">
					<?php foreach($templ_pages as $pagenr => $pagestart) { ?>
						<?php if ($pagestart === false) { ?>
							<?php echo $pagenr ?>
						<?php } else if ($pagestart + 1 == $first) { ?>
							<span class="page_sel"><?php echo $pagenr ?></span>
						<?php } else { ?>
							<a class="page_num" href="packages.php?<?php print mkurl('O=' . (	$pagestart)) ?>"><?php echo $pagenr ?></a>
						<?php } ?>
					<?php } ?>
				</div>
			</div> <!-- .page_links -->
		</div> <!-- .pgbox .pkg_search_results_footer -->
	</form>
<?php } # search was successful and returned multiple results ?>
