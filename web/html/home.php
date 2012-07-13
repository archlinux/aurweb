<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
set_lang();
check_sid();

include_once('stats.inc.php');

html_header( __("Home") );

$dbh = db_connect();

?>

<div id="content-left-wrapper">
	<div id="content-left">
		<div id="intro" class="box">
			<h2>AUR <?php print __("Home"); ?></h2>
			<p>
			<?php
			echo __(
				'Welcome to the AUR! Please read the %sAUR User Guidelines%s and %sAUR TU Guidelines%s for more information.',
				'<a href="http://wiki.archlinux.org/index.php/AUR_User_Guidelines">',
				'</a>',
				'<a href="http://wiki.archlinux.org/index.php/AUR_Trusted_User_Guidelines">',
				'</a>'
				);
			?>
			</p>
			<p>
			<?php
			echo __(
				'Contributed PKGBUILDs %smust%s conform to the %sArch Packaging Standards%s otherwise they will be deleted!',
				'<b>', '</b>',
				'<a href="http://wiki.archlinux.org/index.php/Arch_Packaging_Standards">',
				'</a>'
				);
			?>
			</p>
			<p>
			<?php echo __('Remember to vote for your favourite packages!'); ?>
			<?php echo __('Some packages may be provided as binaries in [community].'); ?>
			</p>
			<p>
			<h4><?php echo __('Discussion') ?></h4>
			<?php
			echo __(
				'General discussion regarding the Arch User Repository (AUR) and Trusted User structure takes place on %saur-general%s. This list can be used for package orphan requests, merge requests, and deletion requests. For discussion relating to the development of the AUR, use the %saur-dev%s mailing list.',
				'<a href="http://mailman.archlinux.org/mailman/listinfo/aur-general">',
				'</a>',
				'<a href="http://mailman.archlinux.org/mailman/listinfo/aur-dev">',
				'</a>'
				);
			?>
			</p>
			<h4><?php echo __('Bug Reporting') ?></h4>
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

			<div class="important">
				<b><?php echo __('DISCLAIMER') ?> :</b>
				<br />
				<?php echo __('Unsupported packages are user produced content. Any use of the provided files is at your own risk.'); ?>
			</div>
		</div>
		<?php if (!empty($_COOKIE["AURSID"])): ?>
			<div id="pkg-updates" class="widget box">
				<table>
					<tr>
						<td class="pkg-name">
							<?php
							$userid = uid_from_sid($_COOKIE["AURSID"]);
							user_table($userid, $dbh);
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
		<form id="pkgsearch-form" method="get" action="<?php get_uri('/packages/'); ?>">
			<fieldset>
				<label for="pkgsearch-field">Package Search:</label>
				<input type="hidden" name="O" value="0" />
				<input type="text" name="K" size="30" value="<?php if (isset($_REQUEST["K"])) { print stripslashes(trim(htmlspecialchars($_REQUEST["K"], ENT_QUOTES))); } ?>" maxlength="35" />
			</fieldset>
		</form>
	</div>
	<div id="pkg-updates" class="widget box">
		<table>
			<tr>
				<td class="pkg-name">
					<?php updates_table($dbh); ?>
				</td>
			</tr>
		</table>
	</div>
	<div id="pkg-updates" class="widget box">
		<table>
			<tr>
				<td class="pkg-name">
					<?php general_stats_table($dbh); ?>
				</td>
			</tr>
		</table>
	</div>

</div>
<?php
html_footer(AUR_VERSION);
