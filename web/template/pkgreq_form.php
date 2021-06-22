<div class="box">
	<h2><?= __('Submit Request') ?>: <?= htmlspecialchars($pkgbase_name) ?></h2>
	<p>
		<?= __('Use this form to file a request against package base %s%s%s which includes the following packages:',
			'<strong>', htmlspecialchars($pkgbase_name), '</strong>'); ?>
	</p>
	<ul>
		<?php foreach(pkgbase_get_pkgnames($base_id) as $pkgname): ?>
		<li><?= htmlspecialchars($pkgname) ?></li>
		<?php endforeach; ?>
	</ul>
	<form action="<?= get_uri('/pkgbase/'); ?>" id="request-form" method="post">
		<fieldset>
			<input type="hidden" name="IDs[<?= $base_id ?>]" value="1" />
			<input type="hidden" name="ID" value="<?= $base_id ?>" />
			<input type="hidden" name="token" value="<?= htmlspecialchars($_COOKIE['AURSID']) ?>" />
			<p>
				<label for="id_type"><?= __("Request type") ?>:</label>
				<select name="type" id="id_type" onchange="showHideMergeSection(); showHideRequestHints()">
					<option value="deletion"><?= __('Deletion') ?></option>
					<option value="merge"><?= __('Merge') ?></option>
					<?php if (pkgbase_maintainer_uid($base_id)): ?>
					<option value="orphan"><?= __('Orphan') ?></option>
					<?php endif; ?>
				</select>
			</p>
			<script type="text/javascript" src="/js/typeahead.js"></script>
			<script type="text/javascript">
			function showHideMergeSection() {
				const elem = document.getElementById('id_type');
				const merge_section = document.getElementById('merge_section');
				if (elem.value == 'merge') {
					merge_section.style.display = '';
				} else {
					merge_section.style.display = 'none';
				}
			}

			function showHideRequestHints() {
				document.getElementById('deletion_hint').style.display = 'none';
				document.getElementById('merge_hint').style.display = 'none';
				document.getElementById('orphan_hint').style.display = 'none';

				const elem = document.getElementById('id_type');
				document.getElementById(elem.value + '_hint').style.display = '';
			}

			document.addEventListener('DOMContentLoaded', function() {
				showHideMergeSection();
				showHideRequestHints();

				const input = document.getElementById('id_merge_into');
                                const form = document.getElementById('request-form');
                                const type = "suggest-pkgbase";

				typeahead.init(type, input, form, false);
			});
			</script>
			<p id="merge_section">
				<label for="id_merge_into"><?= __("Merge into") ?>:</label>
				<input type="text" name="merge_into" id="id_merge_into" autocomplete="off"/>
			</p>
			<p>
				<label for="id_comments"><?= __("Comments") ?>:</label>
				<textarea name="comments" id="id_comments" rows="5" cols="50"></textarea>
			</p>
			<p id="deletion_hint">
				<?= __('By submitting a deletion request, you ask a Trusted User to delete the package base. This type of request should be used for duplicates, software abandoned by upstream, as well as illegal and irreparably broken packages.') ?>
			</p>
			<p id="merge_hint">
				<?= __('By submitting a merge request, you ask a Trusted User to delete the package base and transfer its votes and comments to another package base. Merging a package does not affect the corresponding Git repositories. Make sure you update the Git history of the target package yourself.') ?>
			</p>
			<p id="orphan_hint">
				<?= __('By submitting an orphan request, you ask a Trusted User to disown the package base. Please only do this if the package needs maintainer action, the maintainer is MIA and you already tried to contact the maintainer previously.') ?>
			</p>
			<p>
				<input type="submit" class="button" name="do_FileRequest" value="<?= __("Submit Request") ?>" />
			</p>
		</fieldset>
	</form>
</div>
