<form action='packages.php?<?php echo htmlentities($_SERVER['QUERY_STRING']) ?>' method='post'>
<div class="pgbox">
<?php if (!$result) { ?>
<div class='pgboxbody'><?php print __("Error retrieving package list.") ?></div>
<?php } elseif ($total == 0) { ?>
<div class='pgboxbody'><?php print __("No packages matched your search criteria.") ?></div>
<?php } else { ?>
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
$atype = account_from_sid($_COOKIE['AURSID']);
for ($i = 0; $row = mysql_fetch_assoc($result); $i++) {
	(($i % 2) == 0) ? $c = "data1" : $c = "data2";
	if ($row["OutOfDateTS"] !== NULL): $c = "outofdate"; endif;
?>
<tr>
	<?php if ($SID): ?>
	<td class='<?php print $c ?>'><input type='checkbox' name='IDs[<?php print $row["ID"] ?>]' value='1'></td>
	<?php endif; ?>
	<td class='<?php print $c ?>'><span class='f5'><span class='blue'><?php print $row["Category"] ?></span></span></td>
	<td class='<?php print $c ?>'><span class='f4'><a href='packages.php?ID=<?php print $row["ID"] ?>'><span class='black'><?php print $row["Name"] ?> <?php print $row["Version"] ?></span></a></span></td>
	<td class='<?php print $c ?>' style="text-align: right"><span class='f5'><span class='blue'><?php print $row["NumVotes"] ?></span></span></td>
	<?php if ($SID): ?>
	<td class='<?php print $c ?>'><span class='f5'><span class='blue'>
	<?php if (isset($row["Voted"])): ?>
	<?php print __("Yes") ?></span></td>
	<?php else: ?>
	</span></td>
	<?php endif; ?>
	<td class='<?php print $c ?>'><span class='f5'><span class='blue'>
	<?php if (isset($row["Notify"])): ?>
	<?php print __("Yes") ?></span></td>
	<?php else: ?>
	</span></td>
	<?php endif; ?>
	<?php endif; ?>
	<td class='<?php print $c ?>'><span class='f4'><span class='blue'>
	<?php print htmlspecialchars($row['Description'], ENT_QUOTES); ?></span></span></td>
	<td class='<?php print $c ?>'><span class='f5'><span class='blue'>
	<?php if (isset($row["Maintainer"])): ?>
	<a href='packages.php?K=<?php print $row['Maintainer'] ?>&amp;SeB=m'><?php print $row['Maintainer'] ?></a>
	<?php else: ?>
	<span style='color: blue; font-style: italic;'><?php print __("orphan") ?></span>
	<?php endif; ?>
	</span></span></td>
</tr>
<?php } ?>

	</table>
</div>


<div class="pgbox">
	<table width='100%'>
	<tr>
		<td align='left'>
	<div id="legend">
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
		<input type='checkbox' name='confirm_Delete' value='1' /> <?php print __("Confirm") ?>
		<?php endif; ?>
		<input type='submit' class='button' style='width: 80px' value='<?php print __("Go") ?>' />
	</div>
	<?php endif; ?>
		</td>

		<td align='right'>
		<span class='f4'><span class='blue'>
		<?php print __("Showing results %s - %s of %s", $first, $last, $total) ?>
		</span></span>
		<br />

		<div id="pages">
		<?php
			if ($_GET['O'] > 0):
				$O = $_GET['O'] - $_GET['PP'];

				if ($_GET['O'] < $_GET['PP']) {
					$O = 0;
				}
		?>
			<a class="page_num" href="packages.php?<?php print mkurl("O=0") ?>"><?php echo __('First') ?></a>
			<a class="page_num" href="packages.php?<?php print mkurl("O=$O") ?>"><?php echo __('Previous') ?></a>
		<?php   endif; ?>

			<?php
			if ($_GET['PP'] > 0) {
				$pages = ceil($total / $_GET['PP']);
			}

			if ($pages > 1) {
				if ($_GET['O'] > 0) {
					$currentpage = ceil(($_GET['O'] + 1) / $_GET['PP']);
				}
				else {
					$currentpage = 1;
				}

				$morepages = $currentpage + 5;

				print (($currentpage-5) > 1) ? '...' : '';

				# Display links for more search results.
				for ($i = ($currentpage - 5); $i <= $morepages && $i <= $pages; $i++) {
					if ($i < 1) {
						$i = 1;
					}

					$pagestart = ($i - 1) * $_GET['PP'];

					if ($i <> $currentpage) :
					?>
				<a class="page_num" href="packages.php?<?php print mkurl('O=' . ($pagestart)) ?>"><?php echo $i ?></a>
					<?php else : echo "<span id=\"page_sel\">$i</span>";
					endif;
				}

				print ($pages > $morepages) ? '...' : '';
				?>

			<?php if ($total - $_GET['PP'] - $_GET['O'] > 0): ?>
				<a class="page_num" href='packages.php?<?php print mkurl('O=' . ($_GET['O'] + $_GET['PP'])) ?>'><?php echo __('Next') ?></a>
				<a class="page_num" href='packages.php?<?php print mkurl('O=' . ($total - $_GET['PP'])) ?>'><?php echo __('Last') ?></a>
			<?php endif; ?>

			</div>

		</td>
	</tr>

<?php
			}
}
?>
	</table>
</div>
</form>

