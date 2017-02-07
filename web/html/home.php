<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
set_lang();
check_sid();

include_once('stats.inc.php');

if (isset($_COOKIE["AURSID"])) {
	html_header( __("Dashboard") );
} else {
	html_header( __("Home") );
}

?>

<div id="content-left-wrapper">
	<div id="content-left">
		<?php if (isset($_COOKIE["AURSID"])): ?>
		<div id="intro" class="box">
			<h2><?= __("Dashboard"); ?></h2>
			<h3><?= __("My Flagged Packages"); ?></h3>
			<?php
			$params = array(
				'PP' => 50,
				'SeB' => 'M',
				'K' => username_from_sid($_COOKIE["AURSID"]),
				'outdated' => 'on',
				'SB' => 'l',
				'SO' => 'a'
			);
			pkg_search_page($params, false, $_COOKIE["AURSID"]);
			?>
			<h3><?= __("My Requests"); ?></h3>
			<?php
			$results = pkgreq_list(0, 50, uid_from_sid($_COOKIE["AURSID"]));
			$show_headers = false;
			include('pkgreq_results.php');
			?>
		</div>
		<div id="intro" class="box">
			<h2><?= __("My Packages"); ?> <span class="more">(<a href="<?= get_uri('/packages/') ?>?SeB=m&amp;K=<?= username_from_sid($_COOKIE["AURSID"]); ?>"><?= __('more') ?></a>)</span></h2>
			<?php
			$params = array(
				'PP' => 50,
				'SeB' => 'm',
				'K' => username_from_sid($_COOKIE["AURSID"]),
				'SB' => 'l',
				'SO' => 'd'
			);
			pkg_search_page($params, false, $_COOKIE["AURSID"]);
			?>
		</div>
		<div id="intro" class="box">
			<h2><?= __("Co-Maintained Packages"); ?> <span class="more">(<a href="<?= get_uri('/packages/') ?>?SeB=c&amp;K=<?= username_from_sid($_COOKIE["AURSID"]); ?>"><?= __('more') ?></a>)</span></h2>
			<?php
			$params = array(
				'PP' => 50,
				'SeB' => 'c',
				'K' => username_from_sid($_COOKIE["AURSID"]),
				'SB' => 'l',
				'SO' => 'd'
			);
			pkg_search_page($params, false, $_COOKIE["AURSID"]);
			?>
		</div>
		<?php else: ?>
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
			<?= __('AUR packages are user produced content. Any use of the provided files is at your own risk.'); ?>
			</p>
			<p class="readmore"><a href="https://wiki.archlinux.org/index.php/AUR"><?= __('Learn more...') ?></a></p>
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
			<h4><?= __('Submitting Packages') ?></h4>
			<div class="article-content">
			<p>
			<?php
			echo __(
				'Git over SSH is now used to submit packages to the AUR. See the %sSubmitting packages%s section of the Arch User Repository ArchWiki page for more details.',
				'<a href="https://wiki.archlinux.org/index.php/Arch_User_Repository#Submitting_packages">',
				'</a>'
				);
			?>
			</p>
			<?php if (config_section_exists('fingerprints')): ?>
			<p>
				<?= __('The following SSH fingerprints are used for the AUR:') ?>
			</p>
			<ul>
				<?php foreach (config_items('fingerprints') as $type => $fingerprint): ?>
				<li><code><?= htmlspecialchars($type) ?></code>: <code><?= htmlspecialchars($fingerprint) ?></code></li>
				<?php endforeach; ?>
			</ul>
			<?php endif; ?>
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
				'If you find a bug in the AUR web interface, please fill out a bug report on our %sbug tracker%s. Use the tracker to report bugs in the AUR web interface %sonly%s. To report packaging bugs contact the package maintainer or leave a comment on the appropriate package page.',
				'<a href="https://bugs.archlinux.org/index.php?project=2">',
				'</a>',
				'<strong>',
				'</strong>'
				);
			?>
			</p>
			</div>
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
	<?php if (isset($_COOKIE["AURSID"])): ?>
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
