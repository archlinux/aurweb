<div class="pgbox">
<?php
$uid = uid_from_sid($SID);
while (list($indx, $carr) = each($comments)) { ?>
	<div class="comment-header"><?php

	if ($SID) {
		$carr['UserName'] = "<a href=\"account.php?Action=AccountInfo&amp;ID={$carr['UsersID']}\">{$carr['UserName']}</a>";
	}

	$commentHeader =__('Comment by: %s on %s', $carr['UserName'], gmdate('r', $carr['CommentTS']));

	if (canDeleteCommentArray($carr, $atype, $uid)) {
		$durl = '<form method="POST" action="packages.php?ID='.$row['ID'].'">';
		$durl.= '<input type="hidden" name="action" value="do_DeleteComment">';
		$durl.= '<input type="hidden" name="comment_id" value="'.$carr['ID'].'">';
		$durl.= '<input type="image" src="images/x.png" border="0" ';
		$durl.= ' alt="'.__("Delete comment").'" name="submit" value="1" ';
		$durl.= ' width="19" height="18">&nbsp;';

		$commentHeader = $durl.$commentHeader."</form>";
	}

	echo $commentHeader;
?></div>
	<blockquote class="comment-body">
	<div>
<?php echo nl2br(htmlspecialchars($carr['Comments'])) ?>
	</div>
	</blockquote>
<?php
}
?>
</div>

<?php
$count = package_comments_count($_GET['ID']);
if ($count > 10 && !isset($_GET['comments'])) {
	echo '<div class="pgbox">';
	echo '<a href="'. $_SERVER['PHP_SELF'] . '?ID=' . $_REQUEST['ID'] . '&comments=all">'. __('Show all %s comments', $count) . '</a>';
	echo '</div>';
}
?>
