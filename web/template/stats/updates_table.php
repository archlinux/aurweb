<table class="boxSoft">
<tr>
<th colspan="2" class="boxSoftTitle" style="text-align: right">
<span class="f3"><?php print __("Recent Updates") ?><span class="f5"></span></span>
<a href="rss.php"><img src="images/feed-icon-14x14.png" alt="RSS Feed" /></a>
</th>
</tr>

<?php foreach ($newest_packages->getIterator() as $row): ?>
<tr>
<td class="boxSoft">
<span class="f4"><span class="blue">
<a href="packages.php?ID=<?php print intval($row["ID"]); ?>">
<?php print $row["Name"] . ' ' . $row["Version"]; ?>
</a></span></span>
</td>
<td class="boxSoft">

<?php
$mod_int = intval($row["ModifiedTS"]);
$sub_int = intval($row["SubmittedTS"]);

if ($mod_int == $sub_int):
  $modstring = '<img src="images/new.gif" alt="New!" /> ' . gmdate("r", $sub_int);
else:
  $modstring = gmdate("r", $mod_int);
endif;
?>

<span class="f4"><?php print $modstring; ?></span>
</td>
</tr>

<?php endforeach; ?>

</table>
