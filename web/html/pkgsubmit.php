<?
include("aur.inc");         # access AUR common functions
include("submit_po.inc");   # use some form of this for i18n support
set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in
html_header();              # print out the HTML header

print "<center>\n";

# this is the directory that new packages will be uploaded to
#
$UPLOAD_DIR = "/tmp/aur/temp/";
$INCOMING_DIR = "/tmp/aur/incoming/";

if ($_COOKIE["AURSID"]) {
	# track upload errors
	#
	$error = "";

	if ($_REQUEST["pkgsubmit"]) {
		# If this var is set, then the visitor is uploading a file...
		#
		if (!$_REQUEST["pkgname"]) {
			$error = __("You did not specify a package name.");
		} else {
			$pkg_name = escapeshellarg($_REQUEST["pkgname"]);
			$presult = preg_match("/^[a-z][a-z0-9_-]*$/", $pkg_name);
			if ($presult == FALSE || $presult <= 0) {
				# FALSE => error processing regex, 0 => invalid characters
				#
				$error = __("Invalid name: only lowercase letters are allowed.");
			}
		}

		if (!$error) {
			# first, see if this package already exists, and if it can be overwritten
			#	
			$pkg_exists = package_exists($pkg_name);
			if ($pkg_exists) {
				# ok, it exists - should it be overwritten, and does the user have
				# the permissions to do so?
				#
				if (can_overwrite_pkg($pkg_name, $_COOKIE["AURSID"])) {
					if (!$_REQUEST["overwrite"]) {
						$error = __("You did not tag the 'overwrite' checkbox.");
					}
				} else {
					$error = __("You are not allowed to overwrite the %h%s%h package.",
							array("<b>", $pkg_name, "</b>"));
				}
			}
		}

		if (!$error) {
			# no errors checking upload permissions, go ahead and try to process
			# the uploaded package file.
			#

			$upload_file = $UPLOAD_DIR . $pkg_name;
			if (move_uploaded_file($_FILES["pfile"]["tmp_name"], $upload_file)) {
				# ok, we can proceed
				#
				if (file_exists($INCOMING_DIR . $pkg_name)) {
					# blow away the existing file/dir and contents
					#
					rm_rf($INCOMING_DIR . $pkg_name);
				}

			} else {
				# errors uploading file...
				#
				$error = __("Error trying to upload file - please try again.");
			}
		}

		# at this point, we can safely unpack the uploaded file and parse
		# its contents.
		#
		if (!mkdir($INCOMING_DIR.$pkg_name)) {
			$error = __("Could not create incoming directory: %s.",
					array($INCOMING_DIR.$pkg_name));
		} else {
			if (!chdir($INCOMING_DIR.$pkg_name)) {
				$error = __("Could not change directory to %s.",
						array($INCOMING_DIR.$pkg_name));
			} else {
				# try .gz first
				#
				exec("/bin/sh -c 'tar xzf ".$upload_file."'", $retval);
				if (!$retval) {
					# now try .bz2 format
					#
					exec("/bin/sh -c 'tar xjf ".$upload_file."'", $retval);
				}
				if (!$retval) {
					$error = __("Unknown file format for uploaded file.");
				}
			}
		}

		# At this point, if no error exists, the package has been extracted
		# There should be a $INCOMING_DIR.$pkg_name."/".$pkg_name directory
		# if the user packaged it correctly.  However, if the file was
		# packaged without the $pkg_name subdirectory, try and create it
		# and move the package contents into the new sub-directory.
		#
		if (is_dir($INCOMING_DIR.$pkg_name."/".$pkg_name) &&
				is_file($INCOMING_DIR.$pkg_name."/".$pkg_name."/PKGBUILD")) {
			# the files were packaged correctly
			#
			if (!chdir($INCOMING_DIR.$pkg_name."/".$pkg_name)) {
				$error = __("Could not change to directory %s.",
						array($INCOMING_DIR.$pkg_name."/".$pkg_name));
			}
			$pkg_dir = $INCOMING_DIR.$pkg_name."/".$pkg_name;
		} elseif (is_file($INCOMING_DIR.$pkg_name."/PKGBUILD")) {
			# not packaged correctly, but recovery may be possible.
			# try and create $INCOMING_DIR.$pkg_name."/".$pkg_name and
			# move package contents into the new dir
			#
			if (!mkdir($INCOMING_DIR.$pkg_name."/".$pkg_name)) {
				$error = __("Could not create directory %s.",
						array($INCOMING_DIR.$pkg_name."/".$pkg_name));
			} else {
				exec("/bin/sh -c 'mv * ".$pkg_name."'");
				if (!file_exists($INCOMING_DIR.$pkg_name."/".$pkg_name."/PKGBUILD")) {
					$error = __("Error exec'ing the mv command.");
				}
			}
			if (!chdir($INCOMING_DIR.$pkg_name."/".$pkg_name)) {
				$error = __("Could not change to directory %s.",
						array($INCOMING_DIR.$pkg_name."/".$pkg_name));
			}
			$pkg_dir = $INCOMING_DIR.$pkg_name."/".$pkg_name;
		} else {
			# some wierd packaging/extraction error - baal
			#
			$error = __("Error trying to unpack upload - PKGBUILD does not exist.");
		}

		# if no error, get list of directory contents and process PKGBUILD
		#
		if (!$error) {
			# get list of files
			#
			$d = dir($pkg_dir);
			$pkg_contents = array();
			while ($f = $d->read()) {
				if ($f != "." && $f != "..") {
					$pkg_contents[$f] = filesize($f);
				}
			}
			$d->close();

			# process PKGBIULD - remove line concatenation
			#
			$pkgbuild = array();
			$fp = fopen($pkg_dir."/PKGBUILD", "r");
			$line_no = 0;
			$lines = array();
			$continuation_line = 0;
			$current_line = "";
			while (!$feof($fp)) {
				$line = trim(fgets($fp));
				if (substr($line, strlen($line)-1) == "\\") {
					# continue appending onto existing line_no
					#
					$current_line .= substr($line, 0, strlen($line)-1);
					$continuation_line = 1;
				} else {
					# maybe the last line in a continuation, or a standalone line?
					#
					if ($continuation_line) {
						# append onto existing line_no
						#
						$current_line .= $line;
						$lines[$line_no] = $current_line;
						$current_line = "";
					} else {
						# it's own line_no
						#
						$lines[$line_no] = $line;
					}
					$continuation_line = 0;
					$line_no++;
				}
			}
			fclose($fp);

			$seen_build_function = 0;
			while (list($k, $line) = each($lines)) {

				$lparts = explode("=", $line);
				if (count($lparts) == 2) {
					# this is a variable/value pair
					#
					$pkgbuild[$lparts[0]] = $lparts[1];
				} else {
					# either a comment, blank line, continued line, or build function
					#
					if (substr($lparts[0], 0, 5) == "build") {
						$seen_build_function = 1;
					}
				}
				if ($seen_build_function) {break;}
			}

			# some error checking on PKGBUILD contents - just make sure each
			# variable has a value.  This does not do any validity checking
			# on the values, or attempts to fix line continuation/wrapping.
			#
			if (!$seen_build_function) {
				$error = __("Missing build function in PKGBUILD.");
			}
			if (!array_key_exists("md5sums", $pkgbuild)) {
				$error = __("Missing md5sums variable in PKGBUILD.");
			}
			if (!array_key_exists("source", $pkgbuild)) {
				$error = __("Missing source variable in PKGBUILD.");
			}
			if (!array_key_exists("url", $pkgbuild)) {
				$error = __("Missing url variable in PKGBUILD.");
			}
			if (!array_key_exists("pkgdesc", $pkgbuild)) {
				$error = __("Missing pkgdesc variable in PKGBUILD.");
			}
			if (!array_key_exists("pkgrel", $pkgbuild)) {
				$error = __("Missing pkgrel variable in PKGBUILD.");
			}
			if (!array_key_exists("pkgver", $pkgbuild)) {
				$error = __("Missing pkgver variable in PKGBUILD.");
			}
			if (!array_key_exists("pkgname", $pkgbuild)) {
				$error = __("Missing pkgname variable in PKGBUILD.");
			}
		}

		# update the backend database if there are no errors
		#
		if (!$error) {
			$dbh = db_connect();
			if ($pkg_exists) {

				# TODO add some kind of package history table - for who
				# was the last person to upload, a timestamp, and maybe a
				# comment about it too

				# this is an overwrite of an existing package, the database ID
				# needs to be preserved so that any votes are retained.  However,
				# PackageDepends, PackageSources, and PackageContents can be
				# purged.
				#
				$q = "SELECT * FROM Packages ";
				$q.= "WHERE Name = '".mysql_escape_string($_FILES["pfile"]["name"])."'";
				$result = db_query($q, $dbh);
				$pdata = mysql_fetch_assoc($result);

				# flush out old data that will be replaced with new data
				#
				$q = "DELETE FROM PackageContents WHERE PackageID = ".$pdata["ID"];
				db_query($q, $dbh);
				$q = "DELETE FROM PackageDepends WHERE PackageID = ".$pdata["ID"];
				db_query($q, $dbh);
				$q = "DELETE FROM PackageSources WHERE PackageID = ".$pdata["ID"];
				db_query($q, $dbh);

				# TODO
				# $q = "UPDATE Packages ..."

			} else {
				# this is a brand new package
				#
				# TODO
				# $q = "INSERT ..."
			}
		}

		# TODO clean up on error?  How much cleaning to do?
		#
		if ($error) {
			# TODO clean house (filesystem/database)
			#
		}

	}


	if (!$_REQUEST["pkgsubmit"] || $error) {
		# User is not uploading, or there were errors uploading - then
		# give the visitor the default upload form
		#
		if (ini_get("file_uploads")) {
			if ($error) {
				print "<span class='error'>".$error."</span><br />\n";
				print "<br />&nbsp;<br />\n";
			}
			print "<form action='/pkgsubmit.php' method='post'";
			print "	enctype='multipart/form-data'>\n";
			print "<input type='hidden' name='pkgsubmit' value='1' />\n";
			print "<input type='hidden' name='MAX_FILE_SIZE' value='";
			print initeger(ini_get("upload_max_filesize"))."' />\n";
			print "<table border='0' cellspacing='5'>\n";
			print "<tr>\n";
			print "  <td span='f4' align='right'>";
			print __("Package name").":</td>\n";
			print "  <td span='f4' align='left'>";
			print "<input type='text' name='pkgname' size='30' maxlength='15' />\n";
			print "  </td>\n";
			print "</tr>\n";
			print "<tr>\n";
			print "  <td span='f4' align='right'>";
			print __("Upload package file").":</td>\n";
			print "  <td span='f4' align='left'>";
			print "<input type='file' name='pfile' size='30' />\n";
			print "  </td>\n";
			print "</tr>\n";
			print "<tr>\n";
			print "  <td span='f4' align='right'>";
			print __("Overwrite existing package?");
			print "  </td>\n";
			print "  <td span='f4' align='left'>";
			print "<input type='checkbox' name='overwrite' value='1'> ".__("Yes");
			print "&nbsp;&nbsp;&nbsp;";
			print "<input type='checkbox' name='overwrite' value='0' checked> ";
			print __("No");
			print "  </td>\n";
			print "</tr>\n";

			print "<tr>\n";
			print "  <td>&nbsp;</td>\n";
			print "  <td align='left'>";
			print "<input class='button' type='submit' value='".__("Upload")."' />\n";
			print "</td>\n";
			print "</tr>\n";
			print "</table>\n";

			print "</form>\n";
		} else {
			print __("Sorry, uploads are not permitted by this server.");
			print "<br />\n";
		}
	}

} else {
	# visitor is not logged in
	#
	print __("You must create an account before you can upload packages.");
	print "<br />\n";
}

print "</center>\n";
html_footer("\$Id$");
# vim: ts=2 sw=2 et ft=php
?>
