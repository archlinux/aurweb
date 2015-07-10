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
		<?php
		$date_fmtd = gmdate('Y-m-d H:i', $row['CommentTS']);
		if ($row['UserName']) {
			$user_fmtd = html_format_username($row['UserName']);
			$heading = __('%s commented on %s', $user_fmtd, $date_fmtd);
		} else {
			$heading = __('Anonymous comment on %s', $date_fmtd);
		}

		if ($row['EditedTS']) {
			$date_fmtd = gmdate('Y-m-d H:i', $row['EditedTS']);
			$heading .= ' <span class="edited">(';
			if ($row['DelUsersID']) {
				$user_fmtd = html_format_username($row['DelUserName']);
				$heading .= __('deleted on %s by %s', $date_fmtd, $user_fmtd);
			} else {
				$user_fmtd = html_format_username($row['EditUserName']);
				$heading .= __('last edited on %s by %s', $date_fmtd, $user_fmtd);
			}
			$heading .= ')</span>';
		}

		$row['DelUserName'] = html_format_username($row['DelUserName']);
		$row['EditUserName'] = html_format_username($row['EditUserName']);
		?>
		<h4<?php if ($row['DelUsersID']): ?> class="comment-deleted"<?php endif; ?>>
			<?= $heading ?>
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
			<?php if (!$row['DelUsersID'] && can_edit_comment_array($row)): ?>
			<a href="<?= htmlspecialchars(get_pkgbase_uri($pkgbase_name) . 'edit-comment/?comment_id=' . $row['ID'], ENT_QUOTES) ?>" class="edit-comment" title="<?= __('Edit comment') ?>"><img src="/images/pencil.min.svg" alt="<?= __('Edit comment') ?>" width="11" height="11"></a>
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
