<?php
$uid = uid_from_sid($SID);
$count = package_comments_count($row['ID']);
$pkgname = $row['Name'];
?>
<div id="news">
	<h3>
		<a href="<?= htmlentities(get_pkg_uri($pkgname), ENT_QUOTES) . '?' . mkurl('comments=all') ?>" title="<?= __('View all %s comments' , $count) ?>"><?= __('Latest Comments') ?></a>
		<span class="arrow"></span>
	</h3>

	<?php while (list($indx, $row) = each($comments)): ?>
		<?php if ($SID):
			$row['UserName'] = "<a href=\"" . get_user_uri($row['UserName']) . "\">{$row['UserName']}</a>";
		endif; ?>
		<h4>
			<?php if (canDeleteCommentArray($row, $atype, $uid)): ?>
				<form method="post" action="<?= htmlspecialchars(get_pkg_uri($pkgname), ENT_QUOTES); ?>">
					<fieldset style="display:inline;">
						<input type="hidden" name="action" value="do_DeleteComment" />
						<input type="hidden" name="comment_id" value="<?= $row['ID'] ?>" />
						<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
						<input type="image" src="/images/x.png" alt="<?= __('Delete comment') ?>" name="submit" value="1" />
					</fieldset>
				</form>
			<?php endif; ?>
			<?= __('Comment by %s', $row['UserName']) ?>
		</h4>
		<p class="timestamp"><?= gmdate('Y-m-d H:i', $row['CommentTS']) ?></p>
		<div class="article-content">
			<p>
				<?= parse_comment($row['Comments']) ?>
			</p>
		</div>
	<?php endwhile; ?>
</div>

<?php if ($count > 10 && !isset($_GET['comments'])): ?>
<div id="news">
	<h3>
		<a href="<?= htmlentities(get_pkg_uri($pkgname), ENT_QUOTES) . '?' . mkurl('comments=all') ?>" title="<?= __('View all %s comments', $count) ?>"><?= __('All comments', $count) ?></a>
	</h3>
</div>
<?php endif; ?>
