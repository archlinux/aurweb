
    <form action='packages.php' method='get'>
    <input type='hidden' name='O' value='0'>

    <center>
    <table cellspacing='3' class='boxSoft'>
    <tr>
      <td class='boxSoftTitle' align='right'>
      <span class='f3'><?php echo __('Search Criteria'); ?></span>
      </td>
    </tr>
    <tr>
      <td class='boxSoft'>
    <table style='width: 100%' align='center'>

    <tr>
    <td align='right'>
    <span class='f5'><span class='blue'><?php echo __('Location'); ?>
    </span></span><br />
      <select name='L'>
      <option value='0'><?php echo __('Any'); ?>

<?php

    // The search form - XXX: split into own function?
    //
    // FIXME: highly fugly. whoever makes this use
    //        less print statements gets a cookie
    // FIXME: ugly html. whoever un-tables this gets
    //        another cookie
    while (list($id, $loc) = each($locs)) {
        if (intval($_REQUEST["L"]) == $id) {
            print "  <option value=".$id." selected> ".$loc."\n";
        } else {
            print "  <option value=".$id."> ".$loc."\n";
        }
    }
    print "  </select>\n";
    print "</td>\n";

    print "<td align='right'>\n";
    print "  <span class='f5'><span class='blue'>".__("Category");
    print "</span></span><br />\n";
    print "  <select name='C'>\n";
    print "  <option value=0> ".__("Any")."\n";
    while (list($id, $cat) = each($cats)) {
        if (intval($_REQUEST["C"]) == $id) {
            print "  <option value=".$id." selected> ".$cat."\n";
        } else {
            print "  <option value=".$id."> ".$cat."\n";
        }
    }
    print "  </select>\n";
    print "</td>\n";

    print "<td align='right'>\n";
    print "  <span class='f5'><span class='blue'>".__("Keywords");
    print "</span></span><br />\n";
    print "  <input type='text' name='K' size='20'";

    $K = trim(htmlspecialchars($_REQUEST["K"], ENT_QUOTES));
    print " value=\"".stripslashes($K)."\" maxlength='35'>\n";
    print "</td>\n";

    print "<td align='right'>\n";
    print "  <span class='f5'><span class='blue'>".__("Search by");
    print "</span></span><br />\n";

    print "  <select name='SeB'>\n";
    # by name/description
    print "  <option value=nd";
    $_REQUEST["SeB"] == "nd" ? print " selected> " : print "> ";
    print __("Name")."</option>\n";
    # by maintainer
    print "  <option value=m";
    $_REQUEST["SeB"] == "m" ? print " selected> " : print "> ";
    print __("Maintainer")."</option>\n";
    print "  <option value=s";
    $_REQUEST["SeB"] == "s" ? print " selected> " : print "> ";
    print __("Submitter")."</option>\n";

    print "  </select>\n";
    print "</td>\n";

    print "<td align='right'>\n";
    print "  <span class='f5'><span class='blue'>".__("Per page");
    print "</span></span><br />\n";
    print "  <select name='PP'>\n";
    print "  <option value=25";
    $PP == 25 ? print " selected> 25\n" : print "> 25\n";
    print "  <option value=50";
    $PP == 50 ? print " selected> 50\n" : print "> 50\n";
    print "  <option value=75";
    $PP == 75 ? print " selected> 75\n" : print "> 75\n";
    print "  <option value=100";
    $PP == 100 ? print " selected> 100\n" : print "> 100\n";
    print "  </select>\n";
    print "</td>\n";

    // Added to break put the buttons in a new line
?>
    </tr></table><center><table><tr>

    <td align='right' valign='bottom'>&nbsp;
      <input type='submit' style='width:80px' class='button' name='do_Search'
    value='<?php echo __('Go'); ?>'>
    </td>

    <td align='right' valign='bottom'>&nbsp;
      <input type='submit' style='width:80px'  class='button' name='do_Orphans'
	      value='<?php echo __('Orphans'); ?>'>
    </td>

    </tr>
    </table>

      </td>
    </tr>
    </table>
    </center>
    </form>
    <br />

