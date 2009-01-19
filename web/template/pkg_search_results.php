<?php
# Encode search string
$_GET['K'] = urlencode($_GET['K']);
?>
<form action='packages.php?<?php print $_SERVER['QUERY_STRING'] ?>' method='post'>
<center>

<table cellspacing='3' class='boxSoft'>
	<tr>
		<td class='boxSoftTitle' align='right'>
			<span class='f3'><?php print __("Package Listing") ?></span>
		</td>
	</tr>
	<tr>
		<td class='boxSoft'>
			<table width='100%' cellspacing='0' cellpadding='2'>

<?php if (!$result) { ?>
<div class='pgboxbody'><?php print __("Error retrieving package list.") ?></div>
<?php } elseif ($total == 0) { ?>
<div class='pgboxbody'><?php print __("No packages matched your search criteria.") ?></div>
<?php } else { ?>

<tr>
	<?php if ($SID): ?>
	<th style='border-bottom: #666 1px solid; vertical-align: bottom'>&nbsp;</th>
	<?php endif; ?>
	<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'>
		<a href='?<?php print mkurl('SB=l&SO=' . $SO_next) ?>'><?php print __("Location") ?></a>
	</span></th>
	<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'>
		<a href='?<?php print mkurl('SB=c&SO=' . $SO_next) ?>'><?php print __("Category") ?></a>
	</span></th>
	<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'>
		<a href='?<?php print mkurl('SB=n&SO=' . $SO_next) ?>'><?php print __("Name") ?></a>
	</span></th>
	<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'>
		<a href='?<?php print mkurl('SB=v&SO=' . $SO_next) ?>'><?php print __("Votes") ?></a>
	</span></th>
	<?php if ($SID): ?>
	<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'><?php print __("Voted") ?></span></th>
	<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'><?php print __("Notify") ?></span></th>
	<?php endif; ?>
	<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'><?php print __("Description") ?></a></span></th>
	<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'>
		<a href='?<?php print mkurl('SB=m&SO=' . $SO_next) ?>'><?php print __("Maintainer") ?></a>
	</span></th>
</tr>

<?php
$atype = account_from_sid($_COOKIE['AURSID']);
for ($i = 0; $row = mysql_fetch_assoc($result); $i++) {
	(($i % 2) == 0) ? $c = "data1" : $c = "data2";
	if ($row["OutOfDate"]): $c = "outofdate"; endif;
?>
<tr>
	<?php if ($SID): ?>
	<td class='<?php print $c ?>'><input type='checkbox' name='IDs[<?php print $row["ID"] ?>]' value='1'></td>
	<?php endif; ?>
	<td class='<?php print $c ?>'><span class='f5'><span class='blue'><?php print $row["Location"] ?></span></span></td>
	<td class='<?php print $c ?>'><span class='f5'><span class='blue'><?php print $row["Category"] ?></span></span></td>
	<td class='<?php print $c ?>'><span class='f4'><a href='packages.php?ID=<?php print $row["ID"] ?>'><span class='black'><?php print $row["Name"] ?> <?php print $row["Version"] ?></span></a></span></td>
	<td class='<?php print $c ?>'><span class='f5'><span class='blue'>&nbsp;&nbsp;&nbsp;<?php print $row["NumVotes"] ?></span></span></td>
	<?php if ($SID): ?>
	<td class='<?php print $c ?>'><span class='f5'><span class='blue'>
	<?php if (isset($row["Voted"])): ?>
	&nbsp;&nbsp;<?php print __("Yes") ?></span></td>
	<?php else: ?>
	&nbsp;</span></td>
	<?php endif; ?>
	<td class='<?php print $c ?>'><span class='f5'><span class='blue'>
	<?php if (isset($row["Notify"])): ?>
	&nbsp;&nbsp;<?php print __("Yes") ?></span></td>
	<?php else: ?>
	&nbsp;</span></td>
	<?php endif; ?>
	<?php endif; ?>
	<td class='<?php print $c ?>'><span class='f4'><span class='blue'>
	<?php print $row["Description"] ?></span></span></td>
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
		</td>
	</tr>
</table>

<?php if ($SID): ?>
<div style='text-align: right; padding: 5px 5% 5px 0'>
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
	<input type='submit' class='button' style='width: 80px' value='<?php print __("Go") ?>' />
</div>
<?php endif; ?>

<table width='90%' cellspacing='0' cellpadding='2'>
	<tr>
		<td>
			<table border='0' cellpadding='0' cellspacing='0' width='100%'>
			<tr>
				<td colspan='2' align='center'>
				<span class='f3'>
				<?php echo __('Legend') ?>
				<span class="outofdate"><?php print __('Out of Date') ?></span>
				</span></td>
				<tr><td align='center' colspan='0'><span class='f4'><span class='blue'>
				<?php print __("Showing results %s - %s of %s", $first, $last, $total) ?>
				</span></span></td></tr>
			</tr>
			<?php
			if ($_GET['PP'] > 0) {
				$pages = ceil($total / $_GET['PP']);
			}

			if ($pages > 1) {
			?>

			<tr>
				<td align='center' width='100%'>
				<?php
				if ($_GET['O'] > 0) {
					$currentpage = ceil(($_GET['O'] + 1) / $_GET['PP']);
				}
				else {
					$currentpage = 1;
				}

				for ($i = 1; $i <= $pages; $i++) {
					if ($i <> $currentpage) :
						$pagestart = ($i - 1) * $_GET['PP'];
					?>
				<a href='packages.php?<?php print mkurl('O=' . ($pagestart))?>'><?php print "$i " ?></a>
					<?php else : print "[$i] ";
					endif;
				}
				?>
				</td>
			</tr>

<?php
			}
}
?>

			</table>
		</td>
	</tr>
</table>

</center>
</form>
