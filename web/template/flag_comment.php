<div class="box">
	<h2><?= __('Flagged Out-of-Date Comment: %s', htmlspecialchars($pkgbase_name)) ?></h2>
	<p>
		<?php if (isset($message['Username'])): ?>
			<?= __('%s%s%s flagged %s%s%s out-of-date on %s%s%s for the following reason:',
				'<strong>', html_format_username($message['Username']), '</strong>',
				'<strong>', htmlspecialchars($pkgbase_name), '</strong>',
				'<strong>', date('Y-m-d', $message['OutOfDateTS']), '</strong>'); ?>
		<?php else: ?>
			<?= __('%s%s%s is not flagged out-of-date.',
				'<strong>', htmlspecialchars($pkgbase_name), '</strong>'); ?>
		<?php endif; ?>
	</p>
	<p>
		<div class="article-content">
			<blockquote><p><?= parse_comment($message['FlaggerComment']) ?></p></blockquote>
		</div>
	</p>
	<p>
		<form action="<?= htmlspecialchars(get_pkgbase_uri($pkgbase_name), ENT_QUOTES) ?>">
			<input type="submit" value="<?= __("Return to Details") ?>" />
		</form>
	</p>
</div>

