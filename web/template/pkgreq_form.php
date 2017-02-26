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
	<form action="<?= get_uri('/pkgbase/'); ?>" method="post">
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
			<script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/1.8.2/jquery.min.js"></script>
			<script type="text/javascript" src="/js/bootstrap-typeahead.min.js"></script>
			<script type="text/javascript">
			function showHideMergeSection() {
				if ($('#id_type').val() == 'merge') {
					$('#merge_section').show();
				} else {
					$('#merge_section').hide();
				}
			}

			function showHideRequestHints() {
				$('#deletion_hint').hide();
				$('#merge_hint').hide();
				$('#orphan_hint').hide();
				$('#' + $('#id_type').val() + '_hint').show();
			}

			$(document).ready(function() {
				showHideMergeSection();
				showHideRequestHints();

				$('#id_merge_into').typeahead({
					source: function(query, callback) {
						$.getJSON('<?= get_uri('/rpc'); ?>', {type: "suggest-pkgbase", arg: query}, function(data) {
							callback(data);
						});
					},
					matcher: function(item) { return true; },
					sorter: function(items) { return items; },
					menu: '<ul class="pkgsearch-typeahead"></ul>',
					items: 20
				}).attr('autocomplete', 'off');
			});
			</script>
			<p id="merge_section">
				<label for="id_merge_into"><?= __("Merge into") ?>:</label>
				<input type="text" name="merge_into" id="id_merge_into" />
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
