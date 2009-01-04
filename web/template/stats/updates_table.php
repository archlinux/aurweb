<table class="boxSoft">
<tr>
<th colspan="2" class="boxSoftTitle" style="text-align: right">
<a href="rss2.php"><img src="images/rss.gif"></a>
<span class="f3"><?php print __("Recent Updates") ?><span class="f5"></span></span>
</th>
</tr>

<?php foreach ($newest_packages->getIterator() as $row): ?>
<tr>
<td class="boxSoft">
<span class="f4"><span class="blue">
<a href="packages.php?ID=<?php print intval($row["ID"]); ?>">
<?php print $row["Name"] . ' ' . $row["Version"]; ?>
</a></span>
</td>
<td class="boxSoft">

<?php
$mod_int = intval($row["ModifiedTS"]);
$sub_int = intval($row["SubmittedTS"]);

if ($mod_int != 0):
  $modstring = gmdate("r", $mod_int);
elseif ($sub_int != 0):
  $modstring = '<img src="images/new.gif" /> ' . gmdate("r", $sub_int);
else:
  $modstring = '(unknown)';
endif;
?>

<span class="f4"><?php print $modstring; ?></span>
</td>
</tr>

<?php endforeach; ?>

</table>

