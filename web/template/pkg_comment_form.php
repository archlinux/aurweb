	<form action="<?= get_pkgbase_uri($pkgbase_name) ?>" method="post">
		<fieldset>
			<div>
				<input type="hidden" name="action" value="<?= (isset($comment_id)) ? "do_EditComment" : "do_AddComment" ?>" />
				<input type="hidden" name="ID" value="<?= intval($base_id) ?>" />
				<?php if (isset($comment_id)): ?>
				<input type="hidden" name="comment_id" value="<?= $comment_id ?>" />
				<?php endif; ?>
				<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
			</div>
			<p>
				<?= __("Git commit identifiers referencing commits in the AUR package repository and URLs are converted to links automatically.") ?>
				<?= __("%sMarkdown syntax%s is partially supported.", '<a href="https://daringfireball.net/projects/markdown/syntax">', "</a>") ?>
			</p>
			<p>
				<textarea id="id_comment" name="comment" cols="80" rows="10"><?= (isset($comment_id)) ? htmlspecialchars($comment) : "" ?></textarea>
			</p>
			<p>
				<input type="submit" value="<?= (isset($comment_id)) ? __("Save") : __("Add Comment") ?>" />
				<?php if (!isset($comment_id) && !pkgbase_user_notify($uid, $base_id)): ?>
					<span class="comment-enable-notifications">
						<input type="checkbox" name="enable_notifications" id="id_enable_notifications" />
						<label for="id_enable_notifications"><?= __("Enable notifications") ?></label>
					</span>
				<?php endif; ?>
			</p>
		</fieldset>
	</form>
