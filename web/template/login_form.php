<?php
include_once('acctfuncs.inc');
$login = try_login();
$login_error = $login['error'];
?>

<span id="login_bar">
  <?php
  if (isset($_COOKIE["AURSID"])) {
    print __("Logged-in as: %h%s%h", array("<b>", username_from_sid($_COOKIE["AURSID"]), "</b>"));
?>
<br /><a href="/logout.php"><?php print __("Logout"); ?></a>
<?php
  }
  else {
    if ($login_error) {
      print "<span class='error'>" . $login_error . "</span><br />\n";
    } 
  ?>
  <form method="post">
    <label><?php print __('Username') . ':'; ?></label>
    <input type="text" name="user" size="30" maxlength="<?php print USERNAME_MAX_LEN; ?>" value="<?php
      if (isset($_POST['user'])) {
        print htmlspecialchars($_POST['user'], ENT_QUOTES);
      } ?>" />
    <label><?php print __('Password') . ':'; ?></label>
    <input type="password" name="passwd" size="30" maxlength="<?php print PASSWD_MAX_LEN; ?>" />
    <input type="checkbox" name="remember_me" /><?php print __("Remember me"); ?>
    <input type="submit" class="button" value="<?php  print __("Login"); ?>" />
  </form>
  <?php } ?>
</span>

