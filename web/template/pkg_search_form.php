<?php
include_once('pkgfuncs.inc.php');

$searchby = array(
	'nd' => __('Name, Description'),
	'n' => __('Name Only'),
	'x' => __('Exact name'),
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
	'c' => __('Category'),
	'v' => __('Votes'),
	'w' => __('Voted'),
	'o' => __('Notify'),
	'm' => __('Maintainer'),
	'a' => __('Age')
);

$orderby = array(
	'a' => __('Ascending'),
	'd' => __('Descending')
);

$per_page = array(50, 100, 250);
?>

<div id="pkglist-search" class="box filter-criteria">
<h2><?php print __("Search Criteria"); ?></h2>

<form action='<?php echo get_uri('/packages/'); ?>' method='get'>
	<p><input type='hidden' name='O' value='0' /></p>

	<fieldset>
		<legend><?php echo __('Enter search criteria') ?></legend>
		<div>
			<label for="id_category"><?php print __("Category"); ?></label>
			<select name='C' id="id_category">
				<option value='0'><?php print __("Any"); ?></option>
				<?php foreach (pkgCategories() as $id => $cat): ?>
				<?php if (isset($_REQUEST['C']) && $_REQUEST['C'] == $id): ?>
				<option value="<?php print $id ?>" selected="selected"><?php print $cat; ?></option>
				<?php else: ?>
				<option value="<?php print $id ?>"><?php print $cat; ?></option>
				<?php endif; ?>
				<?php endforeach; ?>
			</select>
		</div>
		<div>
			<label for="id_method"><?php print __("Search by"); ?></label>
			<select name='SeB'>
				<?php foreach ($searchby as $k => $v): ?>
				<?php if (isset($_REQUEST['SeB']) && $_REQUEST['SeB'] == $k): ?>
				<option value="<?php print $k; ?>" selected="selected"><?php print $v; ?></option>
				<?php else: ?>
				<option value="<?php print $k; ?>"><?php print $v; ?></option>
				<?php endif; ?>
				<?php endforeach; ?>
			</select>
		</div>
		<div>
			<label for="id_q"><?php print __("Keywords"); ?></label>
			<input type='text' name='K' size='30' value="<?php if (isset($_REQUEST["K"])) { print stripslashes(trim(htmlspecialchars($_REQUEST["K"], ENT_QUOTES))); } ?>" maxlength='35' />
		</div>
		<div>
			<label for="id_out_of_date"><?php echo __('Out of Date'); ?></label>
			<select name='outdated'>
				<?php foreach ($outdated_flags as $k => $v): ?>
				<?php if (isset($_REQUEST['outdated']) && $_REQUEST['outdated'] == $k): ?>
				<option value='<?php print $k; ?>' selected="selected"><?php print $v; ?></option>
				<?php else: ?>
				<option value='<?php print $k; ?>'><?php print $v; ?></option>
				<?php endif; ?>
				<?php endforeach; ?>
			</select>
		</div>
		<div>
			<label for="id_sort_by"><?php print __("Sort by"); ?></label>
			<select name='SB'>
				<?php foreach ($sortby as $k => $v): ?>
				<?php if (isset($_REQUEST['SB']) && $_REQUEST['SB'] == $k): ?>
				<option value='<?php print $k; ?>' selected="selected"><?php print $v; ?></option>
				<?php else: ?>
				<option value='<?php print $k; ?>'><?php print $v; ?></option>
				<?php endif; ?>
				<?php endforeach; ?>
			</select>
		</div>
		<div>
			<label for="id_order_by"><?php print __("Sort order"); ?></label>
			<select name='SO'>
				<?php foreach ($orderby as $k => $v): ?>
				<?php if (isset($_REQUEST['SO']) && $_REQUEST['SO'] == $k): ?>
				<option value='<?php print $k; ?>' selected="selected"><?php print $v; ?></option>
				<?php else: ?>
				<option value='<?php print $k; ?>'><?php print $v; ?></option>
				<?php endif; ?>
				<?php endforeach; ?>
			</select>
		</div>
		<div>
			<label for="id_per_page"><?php print __("Per page"); ?></label>
			<select name='PP'>
				<?php foreach ($per_page as $i): ?>
				<?php if (isset($_REQUEST['PP']) && $_REQUEST['PP'] == $i): ?>
				<option value="<?php print $i; ?>" selected="selected"><?php print $i; ?></option>
				<?php else: ?>
				<option value="<?php print $i; ?>"><?php print $i; ?></option>
				<?php endif; ?>
				<?php endforeach; ?>
			</select>
		</div>
		<div>
			<label>&nbsp;</label>
			<input type='submit' class='button' name='do_Search' value='<?php print __("Go"); ?>' />
			<input type='submit' class='button' name='do_Orphans' value='<?php print __("Orphans"); ?>' />
		</div>
	</fieldset>
</form>
</div>
