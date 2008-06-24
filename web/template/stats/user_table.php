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
<span class='f4'><?php print $maintainer_unsupported_count; ?></span>
</td>
</tr>

<?php if ($atype == 'Trusted User'): ?>

<tr>
<td class='boxSoft'>
<span class='f4'><?php print __("Packages in [community]"); ?></span>
</td>
<td class='boxSoft'>
<span class='f4'><?php print $maintainer_community_count; ?></span>
</td>
</tr>

<?php endif; ?>

<tr>
<td class='boxSoft'>
<span class='f4'><?php print __("Out-of-date"); ?></span>
</td>
<td class='boxSoft'>
<span class='f4'><?php print $flagged_outdated ?></span>
</td>
</tr>
</table>

