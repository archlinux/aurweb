<table class='boxSoft'>
<tr>
<th colspan='2' class='boxSoftTitle'>
<span class='f3'><?php print __("My Statistics"); ?></span>
</th>
</tr>
<tr>
<td class='boxSoft'>
<span class='f4'><?php print __("Packages in unsupported"); ?></span>
</td>
<td class='boxSoft'>
<span class='f4'><a href="packages.php?SeB=m&L=2&K=<?php print username_from_sid($_COOKIE["AURSID"]); ?>"> <?php print $maintainer_unsupported_count; ?></a></span>
</td>
</tr>

<?php if (($atype == 'Trusted User') || ($atype == 'Developer')) : ?>

<tr>
<td class='boxSoft'>
<span class='f4'><?php print __("Packages in [community]"); ?></span>
</td>
<td class='boxSoft'>
<span class='f4'><a href="packages.php?SeB=m&L=3&K=<?php print username_from_sid($_COOKIE["AURSID"]); ?>"> <?php print $maintainer_community_count; ?></a></span>
</td>
</tr>

<?php endif; ?>

<tr>
<td class='boxSoft'>
<span class='f4'><?php print __("Out-of-date"); ?></span>
</td>
<td class='boxSoft'>
<span class='f4'><a href="packages.php?SeB=m&OD=on&K=<?php print username_from_sid($_COOKIE["AURSID"]); ?>"> <?php print $flagged_outdated ?></a></span>
</td>
</tr>
</table>

