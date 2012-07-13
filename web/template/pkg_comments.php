<?php
$uid = uid_from_sid($SID);
$count = package_comments_count($_GET['ID']);
?>
<div id="news">
	<h3>
		<a href="<?php echo htmlentities($_SERVER['REQUEST_URI'], ENT_QUOTES) ?>&amp;comments=all" title="<?php echo __('View all %s comments' , $count) ?>"><?php echo __('Latest Comments') ?></a>
		<span class="arrow"></span>
	</h3>

	<?php while (list($indx, $row) = each($comments)): ?>
		<?php if ($SID):
			$row['UserName'] = "<a href=\"<?php echo get_uri('/account/'); ?>?Action=AccountInfo&amp;ID={$row['UsersID']}\">{$row['UserName']}</a>";
		endif; ?>
		<h4>
			<?php if (canDeleteCommentArray($row, $atype, $uid)): ?>
				<form method="post" action="<?php echo get_uri('/packages/'); ?>?ID=<?php echo $row['ID'] ?>">
					<fieldset style="display:inline;">
						<input type="hidden" name="action" value="do_DeleteComment" />
						<input type="hidden" name="comment_id" value="<?php echo $row['ID'] ?>" />
						<input type="hidden" name="token" value="<?php echo htmlspecialchars($_COOKIE['AURSID']) ?>" />
						<input type="image" src="/images/x.png" alt="<?php echo __('Delete comment') ?> name="submit" value="1" />
					</fieldset>
				</form>
			<?php endif; ?>
			<?php echo __('Comment by %s', $row['UserName']) ?>
		</h4>
		<p class="timestamp"><?php echo gmdate('Y-m-d H:i', $row['CommentTS']) ?></p>
		<div class="article-content">
			<p>
				<?php echo parse_comment($row['Comments']) ?>
			</p>
		</div>
	<?php endwhile; ?>
</div>

<?php if ($count > 10 && !isset($_GET['comments'])): ?>
<div id="news">
	<h3>
		<a href="<?php echo $_SERVER['REQUEST_URI'] ?>&amp;comments=all" title="<?php echo __('View all %s comments', $count) ?>"><?php echo __('All comments', $count) ?></a>
	</h3>
</div>
<?php endif; ?>
