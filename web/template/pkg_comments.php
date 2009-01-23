<div class="pgbox">
<table width="100%">
<?php while (list($indx, $carr) = each($comments)) { ?>
	<tr class='boxSoft'>
	<td class='boxSoftTitle' valign='top' style='padding-right: 10' colspan='2'>
	<span class='f3'>
<?php
	if (canDeleteComment($carr['ID'], $atype, $SID)) {
		$durl = '<a href="pkgedit.php?del_Comment=1';
		$durl.= '&comment_id=' . $carr['ID'] . '&ID=' . $row['ID'];
		$durl.= '"><img src="images/x.png" border="0"';
		$durl.= ' alt="' . __("Delete comment") . '"></a> ';

	  echo $durl;
	}
	if ($SID) {
		echo __("Comment by: %s on %s",
			"<a href='account.php?Action=AccountInfo&ID=" . $carr["UsersID"] . "'><b>" . $carr["UserName"] . "</b></a>", gmdate("Y m d [H:i:s]", $carr["CommentTS"]));
	} else {
		echo __("Comment by: %s on %s",
			'<b>' . $carr['UserName'] . '</b>',
			gmdate("Y m d [H:i:s]", $carr["CommentTS"]));
	}
?>
	</span>
	</td>
	</tr>
	<tr>
	<td class="boxSoft">
	<pre><?php echo htmlspecialchars($carr["Comments"]) ?></pre>
	</td>
	</tr>
<?php
}
?>
</table>
</div>
