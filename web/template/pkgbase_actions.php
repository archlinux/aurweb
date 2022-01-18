<div id="detailslinks" class="listing">
	<div id="actionlist">
		<h4><?= __('Package Actions') ?></h4>
		<ul class="small">
			<li>
				<a href="<?= $pkgbuild_uri ?>"><?= __('View PKGBUILD') ?></a> /
				<a href="<?= $log_uri ?>"><?= __('View Changes') ?></a>
			</li>
			<li><a href="<?= $snapshot_uri ?>"><?= __('Download snapshot') ?></a>
			<li><a href="https://wiki.archlinux.org/title/Special:Search?search=<?= urlencode($row['Name']) ?>"><?= __('Search wiki') ?></a></li>
			<li><span class="flagged"><?= $row["OutOfDateTS"] !== NULL ? html_action_link($base_uri . 'flag-comment/', __('Flagged out-of-date (%s)', "$out_of_date_time")) : "" ?></span></li>
			<?php if ($row["OutOfDateTS"] === NULL): ?>
			<li><?= html_action_link($base_uri . 'flag/', __('Flag package out-of-date')) ?></li>
			<?php elseif (($row["OutOfDateTS"] !== NULL) && has_credential(CRED_PKGBASE_UNFLAG, $unflaggers)): ?>
			<li><?= html_action_form($base_uri . 'unflag/', "do_UnFlag", __('Unflag package')) ?></li>
			<?php endif; ?>

			<?php if (pkgbase_user_voted($uid, $base_id)): ?>
			<li><?= html_action_form($base_uri . 'unvote/', "do_UnVote", __('Remove vote')) ?></li>
			<?php else: ?>
			<li><?= html_action_form($base_uri . 'vote/', "do_Vote", __('Vote for this package')) ?></li>
			<?php endif; ?>

			<?php if (pkgbase_user_notify($uid, $base_id)): ?>
			<li><?= html_action_form($base_uri . 'unnotify/', "do_UnNotify", __('Disable notifications')) ?></li>
			<?php else: ?>
			<li><?= html_action_form($base_uri . 'notify/', "do_Notify", __('Enable notifications')) ?></li>
			<?php endif; ?>

			<?php if (has_credential(CRED_PKGBASE_EDIT_COMAINTAINERS, array($row["MaintainerUID"]))): ?>
			<li><?= html_action_link($base_uri . 'comaintainers/', __('Manage Co-Maintainers')) ?></li>
			<?php endif; ?>

			<li><span class="flagged"><?php if ($row["RequestCount"] > 0) { echo _n('%d pending request', '%d pending requests', $row["RequestCount"]); } ?></span></li>
			<li><?= html_action_link($base_uri . 'request/', __('Submit Request')) ?></li>

			<?php if (has_credential(CRED_PKGBASE_DELETE)): ?>
			<li><?= html_action_link($base_uri . 'delete/', __('Delete Package')) ?></li>
			<li><?= html_action_link($base_uri . 'merge/', __('Merge Package')) ?></li>
			<?php endif; ?>

			<?php if ($uid && $row["MaintainerUID"] === NULL): ?>
			<li><?= html_action_form($base_uri . 'adopt/', "do_Adopt", __('Adopt Package')) ?></li>
			<?php elseif (has_credential(CRED_PKGBASE_DISOWN, array_merge(array($row["MaintainerUID"]), pkgbase_get_comaintainer_uids(array($base_id))))): ?>
			<li><?= html_action_form($base_uri . 'disown/', "do_Disown", __('Disown Package')) ?></li>
			<?php endif; ?>
		</ul>
	</div>
</div>
