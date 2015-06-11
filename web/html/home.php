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
			<?php
			echo __(
				'Contributed PKGBUILDs %smust%s conform to the %sArch Packaging Standards%s otherwise they will be deleted!',
				'<strong>', '</strong>',
				'<a href="https://wiki.archlinux.org/index.php/Arch_Packaging_Standards">',
				'</a>'
				);
			?>
			<?= __('Remember to vote for your favourite packages!'); ?>
			<?= __('Some packages may be provided as binaries in [community].'); ?>
			</p>
			<p class="important">
			<?= __('DISCLAIMER') ?>:
			<?= __('Unsupported packages are user produced content. Any use of the provided files is at your own risk.'); ?>
			</p>
			<p class="readmore"><a href="https://wiki.archlinux.org/index.php/AUR">Learn more...</a></p>
		</div>
		<div id="news">
			<h3><a><?= __('Support') ?></a><span class="arrow"></span></h3>
			<h4><?= __('Package Requests') ?></h4>
			<div class="article-content">
			<p>
			<?php
			echo __(
				'There are three types of requests that can be filed in the %sPackage Actions%s box on the package details page:',
				'<var>',
				'</var>'
				);
			?>
			</p>
			<ul>
				<li><em><?= __('Orphan Request') ?></em>: <?= __('Request a package to be disowned, e.g. when the maintainer is inactive and the package has been flagged out-of-date for a long time.') ?></li>
				<li><em><?= __('Deletion Request') ?></em>: <?= __('Request a package to be removed from the Arch User Repository. Please do not use this if a package is broken and can be fixed easily. Instead, contact the package maintainer and file orphan request if necessary.') ?></li>
				<li><em><?= __('Merge Request') ?></em>: <?= __('Request a package to be merged into another one. Can be used when a package needs to be renamed or replaced by a split package.') ?></li>
			</ul>
			<p>
			<?php
			echo __(
				'If you want to discuss a request, you can use the %saur-requests%s mailing list. However, please do not use that list to file requests.',
				'<a href="https://mailman.archlinux.org/mailman/listinfo/aur-requests">',
				'</a>'
				);
			?>
			</p>
			</div>
			<h4><?= __('Discussion') ?></h4>
			<div class="article-content">
			<p>
			<?php
			echo __(
				'General discussion regarding the Arch User Repository (AUR) and Trusted User structure takes place on %saur-general%s. For discussion relating to the development of the AUR web interface, use the %saur-dev%s mailing list.',
				'<a href="https://mailman.archlinux.org/mailman/listinfo/aur-general">',
				'</a>',
				'<a href="https://mailman.archlinux.org/mailman/listinfo/aur-dev">',
				'</a>'
				);
			?>
			</p>
			</div>
			<h4><?= __('Bug Reporting') ?></h4>
			<div class="article-content">
			<p>
			<?php
			echo __(
				'If you find a bug in the AUR web interface, please fill out a bug report on our %sbug tracker%s. Use the tracker to report bugs in the AUR %sonly%s. To report packaging bugs contact the package maintainer or leave a comment on the appropriate package page.',
				'<a href="https://bugs.archlinux.org/index.php?project=2">',
				'</a>',
				'<strong>',
				'</strong>'
				);
			?>
			</p>
			</div>
		</div>
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
	<?php if (!empty($_COOKIE["AURSID"])): ?>
	<div id="pkg-stats" class="widget box">
		<?php user_table(uid_from_sid($_COOKIE["AURSID"])); ?>
	</div>
	<?php endif; ?>

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
html_footer(AURWEB_VERSION);
