<?php
if (isset($row['BaseID'])) {
	/* On a package details page. */
	$base_id = $row['BaseID'];
} else {
	/* On a package base details page. */
	$base_id = $row['ID'];
}
$include_deleted = has_credential(CRED_COMMENT_VIEW_DELETED);
$count = pkgbase_comments_count($base_id, $include_deleted);
?>
<div id="news">
	<h3>
		<a href="<?= htmlentities(get_pkgbase_uri($pkgbase_name), ENT_QUOTES) . '?' . mkurl('comments=all') ?>" title="<?= __('View all comments' , $count) ?> (<?= $count ?>)"><?= __('Latest Comments') ?></a>
		<span class="arrow"></span>
	</h3>

	<?php while (list($indx, $row) = each($comments)): ?>
		<?php if ($row['UserName'] && $SID):
			$row['UserName'] = "<a href=\"" . get_user_uri($row['UserName']) . "\">{$row['UserName']}</a>";
		endif; ?>
		<h4<?php if ($row['DelUsersID']): ?> class="comment-deleted"<?php endif; ?>>
			<?php if ($row['UserName']): ?>
			<?= __('%s commented', $row['UserName']) ?>
			<?php else: ?>
			<?= __('Anonymous comment') ?>
			<?php endif; ?>
			<?= __('on %s', gmdate('Y-m-d H:i', $row['CommentTS'])) ?>
			<?php if ($row['DelUsersID']): ?>
			(<?= __('deleted') ?>)
			<?php endif; ?>
			<?php if (!$row['DelUsersID'] && can_delete_comment_array($row)): ?>
				<form class="delete-comment-form" method="post" action="<?= htmlspecialchars(get_pkgbase_uri($pkgbase_name), ENT_QUOTES); ?>">
					<fieldset style="display:inline;">
						<input type="hidden" name="action" value="do_DeleteComment" />
						<input type="hidden" name="comment_id" value="<?= $row['ID'] ?>" />
						<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
						<input type="image" class="delete-comment" src="/images/x.min.svg" width="11" height="11" alt="<?= __('Delete comment') ?>" title="<?= __('Delete comment') ?>" name="submit" value="1" />
					</fieldset>
				</form>
			<?php endif; ?>
		</h4>
		<div class="article-content<?php if ($row['DelUsersID']): ?> comment-deleted<?php endif; ?>">
			<p>
				<?= parse_comment($row['Comments']) ?>
			</p>
		</div>
	<?php endwhile; ?>
</div>

<?php if ($count > 10 && !isset($_GET['comments'])): ?>
<div id="news">
	<h3>
		<a href="<?= htmlentities(get_pkgbase_uri($pkgbase_name), ENT_QUOTES) . '?' . mkurl('comments=all') ?>" title="<?= __('View all comments') ?> (<?= $count ?>)"><?= __('All comments', $count) ?></a>
	</h3>
</div>
<?php endif; ?>
