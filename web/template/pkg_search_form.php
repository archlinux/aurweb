<?php
include_once('pkgfuncs.inc.php');

$searchby = array(
	'nd' => __('Name, Description'),
	'n' => __('Name Only'),
	'b' => __('Package Base'),
	'N' => __('Exact Name'),
	'B' => __('Exact Package Base'),
	'k' => __('Keywords'),
	'm'  => __('Maintainer'),
	's'  => __('Submitter')
);

$outdated_flags = array(
	'' => __('All'),
	'on' => __('Flagged'),
	'off' => __('Not Flagged')
);

$sortby = array(
	'n' => __('Name'),
	'v' => __('Votes'),
	'p' => __('Popularity'),
	'w' => __('Voted'),
	'o' => __('Notify'),
	'm' => __('Maintainer'),
	'l' => __('Last modified')
);

$orderby = array(
	'a' => __('Ascending'),
	'd' => __('Descending')
);

$per_page = array(50, 100, 250);
?>

<div id="pkglist-search" class="box filter-criteria">
<h2><?= __("Search Criteria"); ?></h2>

<form action='<?= get_uri('/packages/'); ?>' method='get'>
	<p><input type='hidden' name='O' value='0' /></p>

	<fieldset>
		<legend><?= __('Enter search criteria') ?></legend>
		<div>
			<label for="id_method"><?= __("Search by"); ?></label>
			<select name='SeB'>
				<?php foreach ($searchby as $k => $v): ?>
				<?php if (isset($_REQUEST['SeB']) && $_REQUEST['SeB'] == $k): ?>
				<option value="<?= $k; ?>" selected="selected"><?= $v; ?></option>
				<?php else: ?>
				<option value="<?= $k; ?>"><?= $v; ?></option>
				<?php endif; ?>
				<?php endforeach; ?>
			</select>
		</div>
		<div>
			<label for="id_q"><?= __("Keywords"); ?></label>
			<input type='text' name='K' size='30' value="<?php if (isset($_REQUEST["K"])) { print stripslashes(trim(htmlspecialchars($_REQUEST["K"], ENT_QUOTES))); } ?>" maxlength='35' <?= (empty($tokens[1])) ? 'autofocus="autofocus"' : '' ?> />
		</div>
		<div>
			<label for="id_out_of_date"><?= __('Out of Date'); ?></label>
			<select name='outdated'>
				<?php foreach ($outdated_flags as $k => $v): ?>
				<?php if (isset($_REQUEST['outdated']) && $_REQUEST['outdated'] == $k): ?>
				<option value='<?= $k; ?>' selected="selected"><?= $v; ?></option>
				<?php else: ?>
				<option value='<?= $k; ?>'><?= $v; ?></option>
				<?php endif; ?>
				<?php endforeach; ?>
			</select>
		</div>
		<div>
			<label for="id_sort_by"><?= __("Sort by"); ?></label>
			<select name='SB'>
				<?php foreach ($sortby as $k => $v): ?>
				<?php if (isset($_REQUEST['SB']) && $_REQUEST['SB'] == $k): ?>
				<option value='<?= $k; ?>' selected="selected"><?= $v; ?></option>
				<?php else: ?>
				<option value='<?= $k; ?>'><?= $v; ?></option>
				<?php endif; ?>
				<?php endforeach; ?>
			</select>
		</div>
		<div>
			<label for="id_order_by"><?= __("Sort order"); ?></label>
			<select name='SO'>
				<?php foreach ($orderby as $k => $v): ?>
				<?php if (isset($_REQUEST['SO']) && $_REQUEST['SO'] == $k): ?>
				<option value='<?= $k; ?>' selected="selected"><?= $v; ?></option>
				<?php else: ?>
				<option value='<?= $k; ?>'><?= $v; ?></option>
				<?php endif; ?>
				<?php endforeach; ?>
			</select>
		</div>
		<div>
			<label for="id_per_page"><?= __("Per page"); ?></label>
			<select name='PP'>
				<?php foreach ($per_page as $i): ?>
				<?php if (isset($_REQUEST['PP']) && $_REQUEST['PP'] == $i): ?>
				<option value="<?= $i; ?>" selected="selected"><?= $i; ?></option>
				<?php else: ?>
				<option value="<?= $i; ?>"><?= $i; ?></option>
				<?php endif; ?>
				<?php endforeach; ?>
			</select>
		</div>
		<div>
			<label>&nbsp;</label>
			<input type='submit' class='button' name='do_Search' value='<?= __("Go"); ?>' />
			<input type='submit' class='button' name='do_Orphans' value='<?= __("Orphans"); ?>' />
		</div>
	</fieldset>
</form>
</div>
