<div class="pgbox">
	<form action="packages.php?ID=<?php echo $row['ID'] ?>" method="post">
		<fieldset>
			<input type='hidden' name='IDs[<?php echo $row['ID'] ?>]' value='1' />
			<input type='hidden' name='ID' value="<?php echo $row['ID'] ?>" />
<?php
		# Voting Button
		#
		$q = "SELECT * FROM PackageVotes WHERE UsersID = ". $uid;
		$q.= " AND PackageID = ".$row["ID"];
		$result = db_query($q, $dbh);
		if ($result) {
			if (!mysql_num_rows($result)) {
				echo "      <input type='submit' class='button' name='do_Vote'";
				echo " value='".__("Vote")."' /> ";
			} else {
				echo "<input type='submit' class='button' name='do_UnVote'";
				echo " value='".__("UnVote")."' /> ";
			}
		}

		# Comment Notify Button
		#
		$q = "SELECT * FROM CommentNotify WHERE UserID = ". $uid;
		$q.= " AND PkgID = ".$row["ID"];
		$result = db_query($q, $dbh);
		if ($result) {
			if (!mysql_num_rows($result)) {
				echo "<input type='submit' class='button' name='do_Notify'";
				echo " value='".__("Notify")."' title='".__("New Comment Notification")."' /> ";
			} else {
				echo "<input type='submit' class='button' name='do_UnNotify'";
				echo " value='".__("UnNotify")."' title='".__("No New Comment Notification")."' /> ";
			}
		}

		if ($row["OutOfDateTS"] === NULL) {
			echo "<input type='submit' class='button' name='do_Flag'";
			echo " value='".__("Flag Out-of-date")."' />\n";
		} else {
			echo "<input type='submit' class='button' name='do_UnFlag'";
			echo " value='".__("UnFlag Out-of-date")."' />\n";
		}
			
		if ($row["MaintainerUID"] === NULL) {
			echo "<input type='submit' class='button' name='do_Adopt'";
			echo " value='".__("Adopt Packages")."' />\n";
		} else if ($uid == $row["MaintainerUID"] ||
			$atype == "Trusted User" || $atype == "Developer") {
			echo "<input type='submit' class='button' name='do_Disown'";
			echo " value='".__("Disown Packages")."' />\n";
		}
			
		if ($atype == "Trusted User" || $atype == "Developer") {
			echo "<input type='submit' class='button' name='do_Delete'";
			echo " value='".__("Delete Packages")."' />\n";
			echo "<label for='merge_Into'>".__("Merge into")."</label>\n";
			echo "<input type='text' id='merge_Into' name='merge_Into' /> ";
			echo "<input type='checkbox' name='confirm_Delete' value='1' /> ";
			echo __("Confirm")."\n";
		}
?>
		</fieldset>
	</form>
</div>
