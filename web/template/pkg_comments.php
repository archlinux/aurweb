<div class="pgbox">
<?php
$uid = uid_from_sid($SID);
while (list($indx, $carr) = each($comments)) { ?>
	<div class="comment-header"><?php
	if (canDeleteCommentArray($carr, $atype, $uid)) {
		$durl = '<a href="pkgedit.php?del_Comment=1';
		$durl.= '&comment_id=' . $carr['ID'] . '&ID=' . $row['ID'];
		$durl.= '"><img src="images/x.png" border="0"';
		$durl.= ' alt="' . __("Delete comment") . '"></a> ';

		echo $durl;
	}

	if ($SID) {
		$carr['UserName'] = "<a href=\"account.php?Action=AccountInfo&amp;ID={$carr['UsersID']}\">{$carr['UserName']}</a>";
	}

	echo __('Comment by: %s on %s', $carr['UserName'], gmdate('r', $carr['CommentTS']));
?></div>
	<blockquote class="comment-body">
	<div>
<?php echo nl2br(htmlspecialchars($carr['Comments'])) ?>
	</div>
	</blockquote>
<?php
} ?>
</div>
