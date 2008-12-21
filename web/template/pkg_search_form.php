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
    <table style='width: 100%' align='center'>
      <tr>
        <td align='right'>
          <span class='f5'>
            <span class='blue'>
            <?php print __("Location"); ?>
            </span>
          </span>
          <br />
          <select name='L'>
            <option value=0><?php print __("Any"); ?></option>
<?php    
while (list($id, $loc) = each($locs)) {
  if (intval($_REQUEST["L"]) == $id) {
?>
            <option value="<?php print $id; ?>" selected="selected"><?php print $loc; ?></option>
<?php } else { ?>
            <option value="<?php print $id; ?>"><?php print $loc; ?></option>
<?php        
  }
}
?>
          </select>
        </td>
      <td align='right'>
        <span class='f5'>
          <span class='blue'>
          <?php print __("Category"); ?>
          </span>
        </span>
        <br />
        <select name='C'>
          <option value='0'><?php print __("Any"); ?></option>
<?php 
while (list($id, $cat) = each($cats)) {
  if (intval($_REQUEST["C"]) == $id) {
?>
          <option value="<?php print $id ?>" selected="selected"><?php print $cat; ?></option>
<?php } else { ?>
          <option value="<?php print $id ?>"><?php print $cat; ?></option>
<?php
  }
}
?>
        </select>
      </td>
      <td align='right'>
        <span class='f5'>
          <span class='blue'>
          <?php print __("Keywords"); ?>
          </span>
        </span>
        <br />
        <input type='text' name='K' size='20' value="<?php print stripslashes(trim(htmlspecialchars($_REQUEST["K"], ENT_QUOTES))); ?>" maxlength='35' />
      </td>
      <td align='right'>
        <span class='f5'>
          <span class='blue'>
          <?php print __("Search by"); ?>
          </span>
        </span>
        <br />
        <select name='SeB'>
<?php
$searchby = array('nd' => 'Name'
                 ,'m'  => 'Maintainer'
                 ,'s'  => 'Submitter'
                 );

foreach ($searchby as $k => $v) {
  if ($_REQUEST['SeB'] == $k) {
?>
          <option value="<?php print $k; ?>" selected="selected"><?php print __($v); ?></option>
<?php } else { ?>
          <option value="<?php print $k; ?>"><?php print __($v); ?></option>
<?php
  }
}
?>
        </select>
      </td>
      <td align='right'>
        <span class='f5'>
          <span class='blue'>
          <?php print __("Sort by"); ?>
          </span>
        </span>
        <br />
        <select name='SB'>
<?php
$sortby = array('n' => 'Name'
               ,'c' => 'Category'
               ,'l' => 'Location'
               ,'v' => 'Votes'
               ,'m' => 'Maintainer'
               ,'a' => 'Age'
               );

foreach ($sortby as $k => $v) {
  if ($_REQUEST['SB'] == $k) {
?>
          <option value='<?php print $k; ?>' selected="selected"><?php print __($v); ?></option>
<?php } else { ?>
          <option value='<?php print $k; ?>'><?php print __($v); ?></option>
<?php
  }
}
?>
        </select>
      </td>
      <td align='right'>
        <span class='f5'>
          <span class='blue'>
          <?php print __("Sort order"); ?>
          </span>
        </span>
        <br />
        <select name='SO'>
<?php
$orderby = array('a' => 'Ascending'
                ,'d' => 'Descending'
                );

foreach ($orderby as $k => $v) {
  if ($_REQUEST['SO'] == $k) {
?>
          <option value='<?php print $k; ?>' selected="selected"><?php print __($v); ?></option>
<?php } else { ?>
          <option value='<?php print $k; ?>'><?php print __($v); ?></option>
<?php  
  }
}
?>
        </select>
      </td>
      <td align='right'>
        <span class='f5'>
          <span class='blue'>
          <?php print __("Per page"); ?>
          </span>
        </span>
        <br />
        <select name='PP'>
<?php
$pages = array(25, 50, 75, 100);
foreach ($pages as $i) {
  if ($PP == $i) {
?>
          <option value="<?php print $i; ?>" selected="selected"><?php print $i; ?></option>
<?php } else { ?>
          <option value="<?php print $i; ?>"><?php print $i; ?></option>
<?php  
  }
}
?>
        </select>
      </td>
      </tr>
    </table>
    <center>
    <table>
      <tr>
        <td align='right' valign='bottom'>
          <input type='submit' style='width:80px' class='button' name='do_Search' value='<?php print __("Go"); ?>' />
        </td>
        <td align='right' valign='bottom'>
          <input type='submit' style='width:80px'  class='button' name='do_Orphans' value='<?php print __("Orphans"); ?>' />
        </td>
      </tr>
    </table>
    </center> 
  </td>
</tr>
</table>
</center>
</form>
<br />
