<?php
$atype = account_from_sid($SID);
$uid = uid_from_sid($SID);

$pkgid = intval($_REQUEST['ID']);
if ($uid == $row["MaintainerUID"] or
	($atype == "Developer" or $atype == "Trusted User")) {

	$catarr = pkgCategories();
	$edit_cat = "<form method='post' action='packages.php?ID=".$pkgid."'>\n";
	$edit_cat.= "<p>";
	$edit_cat.= "<input type='hidden' name='action' value='do_ChangeCategory' />";
	$edit_cat.= "<span class='f3'>" . __("Category") . ":</span> ";
	$edit_cat.= "<select name='category_id'>\n";
	foreach ($catarr as $cid => $catname) {
		$edit_cat.= "<option value='$cid'";
		if ($cid == $row["CategoryID"]) {
		    $edit_cat.=" selected='selected'";
		}
		$edit_cat.=">".$catname."</option>";
	}
	$edit_cat.= "</select>&nbsp;<input type='submit' value='" . __("Change category") . "' />";
	$edit_cat.= "</p>";
	$edit_cat.= "</form>";

}
else {
	$edit_cat = "<span class='f3'>" . __("Category") . ": " . $row['Category'] . "</span>";
}

if ($row["SubmitterUID"]) {
	$submitter = username_from_id($row["SubmitterUID"]);
	if ($SID) {
		$submitter = '<a href="account.php?Action=AccountInfo&amp;ID=' . htmlspecialchars($row['SubmitterUID'], ENT_QUOTES) . '">' . htmlspecialchars($submitter) . '</a>';
	}

} else {
	$submitter = "None";
}

if ($row["MaintainerUID"]) {
	$maintainer = username_from_id($row["MaintainerUID"]);
	if ($SID) {
		$maintainer = '<a href="account.php?Action=AccountInfo&amp;ID=' . htmlspecialchars($row['MaintainerUID'], ENT_QUOTES) . '">' . htmlspecialchars($maintainer) . '</a>';
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
$out_of_date_time = ($row["OutOfDateTS"] == 0) ? $msg : gmdate("r", intval($row["OutOfDateTS"]));

?>
<div class="pgbox">
	<div class="pgboxtitle"><span class="f3"><?php echo __("Package Details") ?></span></div>
	<div class="pgboxbody">

	<p>
	<span class='f2'><?php echo htmlspecialchars($row['Name']) . ' ' . htmlspecialchars($row['Version']) ?></span><br />
	<span class='f3'><a href="<?php echo htmlspecialchars($row['URL'], ENT_QUOTES) . '">' . $row['URL'] ?></a></span><br />
	<span class='f3'><?php echo htmlspecialchars($row['Description'], ENT_QUOTES); ?></span>
	</p>

	<?php echo $edit_cat ?>

	<p>
	<span class='f3'><?php echo __('Submitter') .': ' . $submitter ?></span><br />
	<span class='f3'><?php echo __('Maintainer') .': ' . $maintainer ?></span><br />
	<span class='f3'><?php echo $votes ?></span>
	</p>

	<p><span class='f3'><?php echo __('License') . ': ' . htmlspecialchars($license) ?></span></p>

	<p>
	<span class='f3'>
	<?php echo __('Last Updated') . ': ' . $updated_time ?><br />
	<?php echo __('First Submitted') . ': '. $submitted_time ?>
	</span>
	</p>

	<p><span class='f3'>
<?php
		$urlpath = URL_DIR . substr($row['Name'], 0, 2) . "/" . $row['Name'];
		print "<a href='$urlpath/" . $row['Name'] . ".tar.gz'>".__("Tarball")."</a> :: ";
		print "<a href='$urlpath/PKGBUILD'>".__("PKGBUILD")."</a></span>";

		if ($row["OutOfDateTS"] !== NULL) {
			echo "<br /><span class='f6'>".__("This package has been flagged out of date.")." (${out_of_date_time})</span>";
		}
?>
	</p>
<?php

	$deps = package_dependencies($row["ID"]);
	$requiredby = package_required($row["Name"]);

	if (count($deps) > 0 || count($requiredby) > 0) {
		echo '<p>';
	}

	if (count($deps) > 0) {
		echo "<span class='boxSoftTitle'><span class='f3'>". __("Dependencies")."</span></span>";

		while (list($k, $darr) = each($deps)) {
			# darr: (DepName, DepCondition, PackageID), where ID is NULL if it didn't exist
			if (!is_null($darr[2])) {
				echo " <a href='packages.php?ID=".$darr[2]."'>".$darr[0].$darr[1]."</a>";
			} else {
				echo " <a href='http://www.archlinux.org/packages/?q=".urlencode($darr[0])."'>".$darr[0].$darr[1]."</a>";
			}
		}

		if (count($requiredby) > 0) {
			echo '<br />';
		}
	}

	if (count($requiredby) > 0) {
		echo "<span class='boxSoftTitle'><span class='f3'>". __("Required by")."</span></span>";

		while (list($k, $darr) = each($requiredby)) {
			# darr: (PackageName, PackageID)
			echo " <a href='packages.php?ID=".$darr[1]."'>".$darr[0]."</a>";
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
				echo "<a href=\"" . htmlspecialchars((isset($src[1]) ? $src[1] : $src[0]), ENT_QUOTES) . "\">" . htmlspecialchars($src[0]) . "</a><br />\n";
			}
			else {
				$src = $src[0];
				# It is presumably an internal source
				echo "<span class='f8'>" . htmlspecialchars($src) . "</span>";
				echo "<br />\n";
			}
		}
?>
	</div>
<?php
	}

?>

	</div>
</div>
