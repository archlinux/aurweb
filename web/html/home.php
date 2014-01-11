<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
set_lang();
check_sid();

include_once('stats.inc.php');

html_header( __("Home") );

?>

<div id="content-left-wrapper">
	<div id="content-left">
		<div id="intro" class="box">
			<h2>AUR <?= __("Home"); ?></h2>
			<p>
			<?php
			echo __(
				'Welcome to the AUR! Please read the %sAUR User Guidelines%s and %sAUR TU Guidelines%s for more information.',
				'<a href="https://wiki.archlinux.org/index.php/AUR_User_Guidelines">',
				'</a>',
				'<a href="https://wiki.archlinux.org/index.php/AUR_Trusted_User_Guidelines">',
				'</a>'
				);
			?>
			</p>
			<p>
			<?php
			echo __(
				'Contributed PKGBUILDs %smust%s conform to the %sArch Packaging Standards%s otherwise they will be deleted!',
				'<strong>', '</strong>',
				'<a href="https://wiki.archlinux.org/index.php/Arch_Packaging_Standards">',
				'</a>'
				);
			?>
			</p>
			<p>
			<?= __('Remember to vote for your favourite packages!'); ?>
			<?= __('Some packages may be provided as binaries in [community].'); ?>
			</p>
			<h4><?= __('Discussion') ?></h4>
			<p>
			<?php
			echo __(
				'General discussion regarding the Arch User Repository (AUR) and Trusted User structure takes place on %saur-general%s. This list can be used for package orphan requests, merge requests, and deletion requests. For discussion relating to the development of the AUR, use the %saur-dev%s mailing list.',
				'<a href="https://mailman.archlinux.org/mailman/listinfo/aur-general">',
				'</a>',
				'<a href="https://mailman.archlinux.org/mailman/listinfo/aur-dev">',
				'</a>'
				);
			?>
			</p>
			<h4><?= __('Bug Reporting') ?></h4>
			<p>
			<?php
			echo __(
				'If you find a bug in the AUR, please fill out a bug report on our %sbug tracker%s. Use the tracker to report bugs in the AUR %sonly%s. To report packaging bugs contact the package maintainer or leave a comment on the appropriate package page.',
				'<a href="https://bugs.archlinux.org/index.php?project=2">',
				'</a>',
				'<strong>',
				'</strong>'
				);
			?>
			</p>

			<h4><?= __('DISCLAIMER') ?></h4>
			<div class="important">
				<?= __('Unsupported packages are user produced content. Any use of the provided files is at your own risk.'); ?>
			</div>
		</div>
		<?php if (!empty($_COOKIE["AURSID"])): ?>
			<div id="pkg-updates" class="widget box">
				<table>
					<tr>
						<td class="pkg-name">
							<?php
							$userid = uid_from_sid($_COOKIE["AURSID"]);
							user_table($userid);
							?>
						</td>
					</tr>
				</table>
			</div>
		<?php endif; ?>
	</div>
</div>
<div id="content-right">
	<div id="pkgsearch" class="widget">
		<form id="pkgsearch-form" method="get" action="<?= get_uri('/packages/'); ?>">
			<fieldset>
				<label for="pkgsearch-field"><?= __('Package Search') ?>:</label>
				<input type="hidden" name="O" value="0" />
				<input id="pkgsearch-field" type="text" name="K" size="30" value="<?php if (isset($_REQUEST["K"])) { print stripslashes(trim(htmlspecialchars($_REQUEST["K"], ENT_QUOTES))); } ?>" maxlength="35" />
			</fieldset>
		</form>
	</div>
	<div id="pkg-updates" class="widget box">
		<?php updates_table(); ?>
	</div>
	<div id="pkg-stats" class="widget box">
		<?php general_stats_table(); ?>
	</div>

</div>
<script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/1.8.2/jquery.min.js"></script>
<script type="text/javascript" src="/js/bootstrap-typeahead.min.js"></script>
<script type="text/javascript">
$(document).ready(function() {
    $('#pkgsearch-field').typeahead({
        source: function(query, callback) {
            $.getJSON('<?= get_uri('/rpc'); ?>', {type: "suggest", arg: query}, function(data) {
                callback(data);
            });
        },
        matcher: function(item) { return true; },
        sorter: function(items) { return items; },
        menu: '<ul class="pkgsearch-typeahead"></ul>',
        items: 20,
        updater: function(item) {
            document.location = '/packages/' + item;
            return item;
	}
    }).attr('autocomplete', 'off');

    $('#pkgsearch-field').keydown(function(e) {
        if (e.keyCode == 13) {
            var selectedItem = $('ul.pkgsearch-typeahead li.active');
            if (selectedItem.length == 0) {
                $('#pkgsearch-form').submit();
            }
        }
    });
});
</script>
<?php
html_footer(AUR_VERSION);
