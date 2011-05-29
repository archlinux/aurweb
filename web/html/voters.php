<?php
set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');
include('aur.inc.php');
include('pkgfuncs.inc.php');

function getvotes($pkgid) {
	$dbh = db_connect();
	$pkgid = mysql_real_escape_string($pkgid);

	$result = db_query("SELECT UsersID,Username FROM PackageVotes LEFT JOIN Users on (UsersID = ID) WHERE PackageID = $pkgid ORDER BY Username", $dbh);
	return $result;
}

$SID = $_COOKIE['AURSID'];

$pkgid = intval($_GET['ID']);
$votes = getvotes($pkgid);
$account = account_from_sid($SID);

if ($account == 'Trusted User' || $account == 'Developer') {
?>
<html>
<body>
<h3><?php echo account_from_sid($SID) ?></h3>
<h2>Votes for <a href="packages.php?ID=<?php echo $pkgid ?>"><?php echo pkgname_from_id($pkgid) ?></a></h2>
<?php
	while ($row = mysql_fetch_assoc($votes)) {
		$uid = $row['UsersID'];
		$username = $row['Username'];
?>
<a href="account.php?Action=AccountInfo&amp;ID=<?php echo $uid ?>">
<?php echo htmlspecialchars($username) ?></a><br />
<?php
	}
?>
</body>
</html>
<?php
}

