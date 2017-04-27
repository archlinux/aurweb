<?php
set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");

$uid = uid_from_sid($_COOKIE["AURSID"]);

if (isset($_POST["accept"]) && $_POST["accept"]) {
	accept_terms($uid, $_POST["rev"]);
	header("Location: " . get_uri('/'));
}

$terms = fetch_updated_terms($uid);
if (!$terms) {
	header("Location: " . get_uri('/'));
}

html_header('AUR ' . __("Terms of Service"));
?>
<div id="dev-login" class="box">
	<h2>AUR <?= __('Terms of Service') ?></h2>
	<?php if (isset($_COOKIE["AURSID"])): ?>
	<form method="post" action="<?= get_uri('/tos') ?>">
		<fieldset>
			<p>
				<?= __("Logged-in as: %s", '<strong>' . username_from_sid($_COOKIE["AURSID"]) . '</strong>'); ?>
			</p>
			<p>
				<?= __("The following documents have been updated. Please review them carefully:"); ?>
			</p>
			<ul>
			<?php foreach($terms as $row): ?>
				<li><a href="<?= htmlspecialchars(sprintf($row["URL"], $row["Revision"]), ENT_QUOTES) ?>"><?= htmlspecialchars($row["Description"]) ?></a> (<?= __('revision %d', $row["Revision"]) ?>)</li>
			<?php endforeach; ?>
			</ul>
			<p>
				<?php foreach($terms as $row): ?>
					<input type="hidden" name="rev[<?= $row["ID"] ?>]" value="<?= $row["Revision"] ?>" />
				<?php endforeach; ?>
				<input type="checkbox" name="accept" /> <?= __("I accept the terms and conditions above."); ?>
			</p>
			<p>
				<input type="submit" name="submit" value="<?= __("Continue") ?>" />
			</p>
		</fieldset>
	</form>
	<?php endif; ?>
</div>
<?php
html_footer(AURWEB_VERSION);
