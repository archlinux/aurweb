<?php include_once('pkgfuncs.inc') ?>

<form action='packages.php' method='get'>
<input type='hidden' name='O' value='0'>
<center>
<table cellspacing='3' class='boxSoft'>
<tr>
	<td class='boxSoftTitle' align='right'>
		<span class='f3'><?php print __("Search Criteria"); ?></span>
	</td>
</tr>
<tr>
	<td class='boxSoft'>
		<div id="search_box" class="blue">
			<label><?php print __("Keywords"); ?></label>
			<input type='text' name='K' size='20' value="<?php print stripslashes(trim(htmlspecialchars($_REQUEST["K"], ENT_QUOTES))); ?>" maxlength='35' />
			<?php if (!$_GET['detail']): ?><input type='submit' style='width:80px' class='button' name='do_Search' value='<?php print __("Go"); ?>' /><?php endif; ?>
			<a href="?<?php print mkurl('detail=' . (($_GET['detail']) ? 0 : 1) ) ?>">Advanced</a>
			<?php if ($_GET['detail']): ?>
			<div id="advanced">
				<input type="hidden" name="detail" value="1" />
				<ul>
					<li>
						<label><?php print __("Location"); ?></label>
						<select name='L'>
							<option value=0><?php print __("Any"); ?></option>
							<?php
							foreach (pkgLocations() as $id => $loc):
								if (intval($_GET["L"]) == $id):
							?>
							<option value="<?php print $id; ?>" selected="selected"><?php print $loc; ?></option>
							<?php else: ?>
							<option value="<?php print $id; ?>"><?php print $loc; ?></option>
							<?php
								endif;
							endforeach;
							?>
						</select>
					</li>
					<li>
						<label><?php print __("Category"); ?></label>
						<select name='C'>
							<option value='0'><?php print __("Any"); ?></option>
							<?php
							foreach (pkgCategories() as $id => $cat):
								if (intval($_GET["C"]) == $id):
							?>
							<option value="<?php print $id ?>" selected="selected"><?php print $cat; ?></option>
							<?php else: ?>
							<option value="<?php print $id ?>"><?php print $cat; ?></option>
							<?php
								endif;
							endforeach;
							?>
						</select>
					</li>
					<li>
					<label><?php print __("Search by"); ?></label>
						<select name='SeB'>
							<?php
							$searchby = array('nd' => 'Name', 'm'  => 'Maintainer', 's'  => 'Submitter');
							foreach ($searchby as $k => $v):
								if ($_REQUEST['SeB'] == $k):
							?>
							<option value="<?php print $k; ?>" selected="selected"><?php print __($v); ?></option>
							<?php else: ?>
							<option value="<?php print $k; ?>"><?php print __($v); ?></option>
							<?php
								endif;
							endforeach;
							?>
						</select>
					</li>
					<li>
						<label><?php print __("Sort by"); ?></label>
						<select name='SB'>
							<?php
							$sortby = array('n' => 'Name', 'c' => 'Category', 'l' => 'Location', 'v' => 'Votes', 'm' => 'Maintainer', 'a' => 'Age');
							foreach ($sortby as $k => $v):
								if ($_REQUEST['SB'] == $k):
							?>
							<option value='<?php print $k; ?>' selected="selected"><?php print __($v); ?></option>
							<?php else: ?>
							<option value='<?php print $k; ?>'><?php print __($v); ?></option>
							<?php
								endif;
							endforeach;
							?>
						</select>
					</li>
					<li>
						<label><?php print __("Sort order"); ?></label>
						<select name='SO'>
							<?php
							$orderby = array('a' => 'Ascending', 'd' => 'Descending');
							foreach ($orderby as $k => $v):
								if ($_REQUEST['SO'] == $k):
							?>
							<option value='<?php print $k; ?>' selected="selected"><?php print __($v); ?></option>
							<?php else: ?>
							<option value='<?php print $k; ?>'><?php print __($v); ?></option>
							<?php
								endif;
							endforeach;
							?>
						</select>
					</li>
					<li>
						<label><?php print __("Per page"); ?></label>
						<select name='PP'>
							<?php
							$pages = array(25, 50, 75, 100);
							foreach ($pages as $i):
								if ($PP == $i):
							?>
							<option value="<?php print $i; ?>" selected="selected"><?php print $i; ?></option>
							<?php else: ?>
							<option value="<?php print $i; ?>"><?php print $i; ?></option>
							<?php
								endif;
							endforeach;
							?>
						</select>
					</li>
				</ul>
				<input type='submit' style='width:80px' class='button' name='do_Search' value='<?php print __("Go"); ?>' />
				<input type='submit' style='width:80px'  class='button' name='do_Orphans' value='<?php print __("Orphans"); ?>' />
			</div>
			<?php endif; ?>
		</div>
	</td>
</tr>
</table>
</center>
</form>
<br />
