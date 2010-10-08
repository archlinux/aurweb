<?php

$pkgid = intval($_REQUEST['ID']);
if ($row["Location"] == "unsupported" and ($uid == $row["MaintainerUID"] or
	($atype == "Developer" or $atype == "Trusted User"))) {

	$edit_cat = "<a href='pkgedit.php?change_Category=1&amp;ID=";
	$edit_cat .= $pkgid ."'>".$row["Category"]."</a>";
	$edit_cat .= " &nbsp;<span class='fix'>(";
	$edit_cat .= __("change category").")</span>";
}
else {
	$edit_cat = $row['Category'];
}

if ($row["MaintainerUID"]) {
	$maintainer = username_from_id($row["MaintainerUID"]);
	if ($SID) {
		$maintainer = '<a href="account.php?Action=AccountInfo&amp;ID=' . $row['MaintainerUID'] . '">' . $maintainer . '</a>';
	}

} else {
	$maintainer = "None";
}

$votes = __('Votes') . ': ' . $row['NumVotes'];
if ($atype == "Developer" or $atype == "Trusted User") {
	$votes = "<a href=\"voters.php?ID=$pkgid\">$votes</a>";
}

# In case of wanting to put a custom message
$msg = __('unknown');
$license = empty($row['License']) ? $msg : $row['License'];

# Print the timestamps for last updates
$updated_time = ($row["ModifiedTS"] == 0) ? $msg : gmdate("r", intval($row["ModifiedTS"]));
$submitted_time = ($row["SubmittedTS"] == 0) ? $msg : gmdate("r", intval($row["SubmittedTS"]));

?>
<div class="pgbox">
	<div class="pgboxtitle"><span class="f3"><?php echo __("Package Details") ?></span></div>
	<div class="pgboxbody">

	<p>
	<span class='f2'><?php echo $row['Name'] . ' ' . $row['Version'] ?></span><br />
	<span class='f3'><a href="<?php echo $row['URL'] . '">' . $row['URL'] ?></a></span><br />
	<span class='f3'><?php echo htmlspecialchars($row['Description'], ENT_QUOTES); ?></span>
	</p>

	<p>
	<span class='f3'><?php echo $row['Location'] . ' :: ' . $edit_cat ?></span><br />
	<span class='f3'><?php echo __('Maintainer') .': ' . $maintainer ?></span><br />
	<span class='f3'><?php echo $votes ?></span>
	</p>

	<p><span class='f3'><?php echo __('License') . ': ' . $license ?></span></p>

	<p>
	<span class='f3'>
	<?php echo __('Last Updated') . ': ' . $updated_time ?><br />
	<?php echo __('First Submitted') . ': '. $submitted_time ?>
	</span>
	</p>

	<p><span class='f3'>
<?php
		if ($row['LocationID'] == 2) {
			$urlpath = URL_DIR . $row['Name'] . '/' . $row['Name'];
			print "<a href='$urlpath.tar.gz'>".__("Tarball")."</a> :: <a href='$urlpath'>".__("Files")."</a> :: <a href='$urlpath/PKGBUILD'>PKGBUILD</a></span>";
		}

		if ($row["OutOfDate"] == 1) {
			echo "<br /><span class='f6'>".__("This package has been flagged out of date.")."</span>";
		}
?>
	</p>
<?php

	# $deps[0] = array('id','name', 'dummy');
	$deps = package_dependencies($row["ID"]);
	$requiredby = package_required($row["ID"]);

	if (count($deps) > 0 || count($requiredby) > 0) {
		echo '<p>';
	}

	if (count($deps) > 0) {

		echo "<span class='boxSoftTitle'><span class='f3'>". __("Dependencies")."</span></span>";

		while (list($k, $darr) = each($deps)) {
			$url = " <a href='packages.php?ID=".$darr[0];
			while(list($k, $var) = each($pkgsearch_vars)) {
				if (($var == "do_Orphans") && $_REQUEST[$var]) {
					$url .= "&".$var."=1";
				} else {
					$url .= "&".$var."=".rawurlencode(stripslashes($_REQUEST[$var]));
				}
			}
			reset($pkgsearch_vars);
			# $darr[3] is the DepCondition
			if ($darr[2] == 0) echo $url."'>".$darr[1].$darr[3]."</a>";
			else echo " <a href='http://archlinux.org/packages/search/?q=".$darr[1]."'>".$darr[1].$darr[3]."</a>";
		}

		if (count($requiredby) > 0) {
			echo '<br />';
		}
	}

	if (count($requiredby) > 0) {

		echo "<span class='boxSoftTitle'><span class='f3'>". __("Required by")."</span></span>";

		while (list($k, $darr) = each($requiredby)) {
			$url = " <a href='packages.php?ID=".$darr[0];
			while(list($k, $var) = each($pkgsearch_vars)) {
				if (($var == "do_Orphans") && $_REQUEST[$var]) {
					$url .= "&amp;" . $var . "=1";
				} else {
					$url .= "&amp;".$var."=".rawurlencode(stripslashes($_REQUEST[$var]));
				}
			}
			reset($pkgsearch_vars);

			# $darr[3] is the DepCondition
			if ($darr[2] == 0) {
				echo $url . "'>" . $darr[1] . $darr[3] . "</a>";
			}
			else {
				print "<a href='http://archlinux.org/packages/search/?q=".$darr[1]."'>".$darr[1].$darr[3]."</a>";
			}
		}

	}

	if (count($deps) > 0 || count($requiredby) > 0) {
		echo '</p>';
	}


	# $sources[0] = 'src';
	$sources = package_sources($row["ID"]);

	if (count($sources) > 0) {

?>
	<div class='boxSoftTitle'><span class='f3'><?php echo __('Sources') ?></span></div>
	<div>
<?php
		while (list($k, $src) = each($sources)) {
			$src = explode('::', $src);
			$parsed_url = parse_url($src[0]);

			if (isset($parsed_url['scheme']) || isset($src[1])) {
				# It is an external source
				echo "<a href=\"" . (isset($src[1]) ? $src[1] : $src[0]) . "\">{$src[0]}</a><br />\n";
			}
			else {
				$src = $src[0];
				# It is presumably an internal source
				if ($row["LocationID"] == 2) {
					echo "<a href='".dirname($row['URLPath'])."/".$row['Name'];
					echo "/$src'>$src</a><br />\n";
				}
			}
		}
?>
	</div>
<?php
	}

?>

	</div>
</div>
