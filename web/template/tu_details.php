<div class="pgbox">
<div class="pgboxtitle"><span class="f3"><?php print __("Proposal Details") ?></span></div>
<div class="pgboxbody">
<?php if ($isrunning == 1) { ?>
<div style='text-align: center; font-weight: bold; color: red'><?php print __("This vote is still running.") ?></div>
<br />
<?php } ?>
User: <b>
<?php if (!empty($row['User'])) { ?>
<a href='packages.php?K=<?php print $row['User'] ?>&amp;SeB=m'><?php print $row['User'] ?></a>
<?php } else { ?>
N/A
<?php } ?>
</b><br />
<?php print __("Submitted: %s by %s", "<b>" . gmdate("r", $row['Submitted']) . "</b>", "<b>" . username_from_id($row['SubmitterID']) . "</b>") ?><br />
<?php print __("End: ") ?><b><?php print gmdate("r", $row['End']) ?></b><br /><br />
<?php print str_replace("\n", "<br />\n", htmlentities($row['Agenda'])) ?><br /><br />
<center>
<table cellspacing='3' class='boxSoft' style='width: 50%'>
</tr>
<tr>
<td class='boxSoft'>
<table width='100%' cellspacing='0' cellpadding='2'>
<tr>
<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'><?php print __("Yes") ?></span></th>
<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'><?php print __("No") ?></span></th>
<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'><?php print __("Abstain") ?></span></th>
<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'><?php print __("Total") ?></span></th>
<th style='border-bottom: #666 1px solid; vertical-align: bottom'><span class='f2'><?php print __("Voted?") ?></span></th>
</tr>
<tr>
<td class='data1'><span class='f5'><span class='blue'><?php print $row['Yes'] ?></span></span></td>
<td class='data1'><span class='f5'><span class='blue'><?php print $row['No'] ?></span></span></td>
<td class='data1'><span class='f5'><span class='blue'><?php print $row['Abstain'] ?></span></span></td>
<td class='data1'><span class='f5'><span class='blue'><?php print ($row['Yes'] + $row['No'] + $row['Abstain']) ?></span></span></td>
<td class='data1'><span class='f5'><span class='blue'>
<?php if ($hasvoted == 0) { ?>
<span style='color: red; font-weight: bold'><?php print __("No") ?></span>
<?php } else { ?>
<span style='color: green; font-weight: bold'><?php print __("Yes") ?></span>
<?php } ?>
</span></span></td>
</tr>
</table>
</table>
</div></div>
<br />
<div class='pgbox'>
<div class='pgboxtitle'><span class='f3'><?php print __("Vote Actions") ?></span></div>
<div class='pgboxbody'>
<?php if ($canvote == 1) { ?>
<center><form action='tu.php?id=<?php print $row['ID'] ?>' method='post'>
<input type='submit' class='button' name='voteYes' value='<?php print __("Yes") ?>'>
<input type='submit' class='button' name='voteNo' value='<?php print __("No") ?>'>
<input type='submit' class='button' name='voteAbstain' value='<?php print __("Abstain") ?>'>
<input type='hidden' name='doVote' value='1'>
</form></center>
<?php } else { ?>
<center><?php print $errorvote ?></center>
<?php } ?>
</div></div>
<br /><center><a href='tu.php'><?php print __("Back") ?></a></center>
