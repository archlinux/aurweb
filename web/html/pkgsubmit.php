<?
include("aur.inc");         # access AUR common functions
include("submit_po.inc");   # use some form of this for i18n support
include("pkgfuncs.inc");    # package functions
set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in
html_header();              # print out the HTML header
print "<center>\n";

# Debugging
$DBUG = 1;

# this is the directory that new packages will be uploaded to
#
$UPLOAD_DIR = "/tmp/aur/temp/";
$INCOMING_DIR = "/tmp/aur/incoming/";


if ($_COOKIE["AURSID"]) {
	# track upload errors
	#
	$error = "";
  if ($DBUG) {
    print "</center><pre>\n";
    print_r($_REQUEST);
    print "</pre><center>\n";
  }

	if ($_REQUEST["pkgsubmit"]) {
		# If this var is set, then the visitor is uploading a file...
		#
		if (!$_REQUEST["pkgname"]) {
			$error = __("You did not specify a package name.");
		} else {
      $pkg_name = str_replace("'", "", $_REQUEST["pkgname"]);
			$pkg_name = escapeshellarg($pkg_name);
      $pkg_name = str_replace("'", "", $pkg_name); # get rid of single quotes
			$presult = preg_match("/^[a-z][a-z0-9_-]*$/", $pkg_name);
			if ($presult == FALSE || $presult <= 0) {
				# FALSE => error processing regex, 0 => invalid characters
				#
				$error = __("Invalid name: only lowercase letters are allowed.");
			}
		}

    if (!$error && (!$_REQUEST["comments"] || $_REQUEST["comments"] == '')) {
      $error = __("You must supply a comment for this upload/change.");
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

    # TODO check to see if the user has the ability to 'change' package
    # attributes such as location and/or category.  Examples: TUs can
    # only add/change packages in Unsupported and the AUR, normal users
    # can only add/change packages in Unsupported.
    #


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
    if (!$error) {
      if (!@mkdir($INCOMING_DIR.$pkg_name)) {
        $error = __("Could not create incoming directory: %s.",
            array($INCOMING_DIR.$pkg_name));
      } else {
        if (!@chdir($INCOMING_DIR.$pkg_name)) {
          $error = __("Could not change directory to %s.",
              array($INCOMING_DIR.$pkg_name));
        } else {
          # try .gz first
          #
          @exec("/bin/sh -c 'tar xzf ".$upload_file."'", $trash, $retval);
          if (!$retval) {
            # now try .bz2 format
            #
            @exec("/bin/sh -c 'tar xjf ".$upload_file."'", $trash, $retval);
          }
          if (!$retval) {
            $error = __("Unknown file format for uploaded file.");
          }
        }
      }
    }

		# At this point, if no error exists, the package has been extracted
		# There should be a $INCOMING_DIR.$pkg_name."/".$pkg_name directory
		# if the user packaged it correctly.  However, if the file was
		# packaged without the $pkg_name subdirectory, try and create it
		# and move the package contents into the new sub-directory.
		#
    if (!$error) {
      if (is_dir($INCOMING_DIR.$pkg_name."/".$pkg_name) &&
          is_file($INCOMING_DIR.$pkg_name."/".$pkg_name."/PKGBUILD")) {
        # the files were packaged correctly
        #
        if (!@chdir($INCOMING_DIR.$pkg_name."/".$pkg_name)) {
          $error = __("Could not change to directory %s.",
              array($INCOMING_DIR.$pkg_name."/".$pkg_name));
        }
        $pkg_dir = $INCOMING_DIR.$pkg_name."/".$pkg_name;
      } elseif (is_file($INCOMING_DIR.$pkg_name."/PKGBUILD")) {
        # not packaged correctly, but recovery may be possible.
        # try and create $INCOMING_DIR.$pkg_name."/".$pkg_name and
        # move package contents into the new dir
        #
        if (!@mkdir($INCOMING_DIR.$pkg_name."/".$pkg_name)) {
          $error = __("Could not create directory %s.",
              array($INCOMING_DIR.$pkg_name."/".$pkg_name));
        } else {
          @exec("/bin/sh -c 'mv * ".$pkg_name."'");
          if (!file_exists($INCOMING_DIR.$pkg_name."/".$pkg_name."/PKGBUILD")) {
            $error = __("Error exec'ing the mv command.");
          }
        }
        if (!@chdir($INCOMING_DIR.$pkg_name."/".$pkg_name)) {
          $error = __("Could not change to directory %s.",
              array($INCOMING_DIR.$pkg_name."/".$pkg_name));
        }
        $pkg_dir = $INCOMING_DIR.$pkg_name."/".$pkg_name;
      } else {
        # some wierd packaging/extraction error - baal
        #
        $error = __("Error trying to unpack upload - PKGBUILD does not exist.");
      }
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
			while (!feof($fp)) {
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

      # Now process the lines and put any var=val lines into the
      # 'pkgbuild' array.  Also check to make sure it has the build()
      # function.
      #
			$seen_build_function = 0;
			while (list($k, $line) = each($lines)) {

				$lparts = explode("=", $line);
				if (count($lparts) == 2) {
					# this is a variable/value pair, strip out
					# array parens and any quoting
					#
					$pkgbuild[$lparts[0]] = str_replace(array("(",")","\"","'"), "",
              $lparts[1]);
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
			} else {
				if ($pkgbuild["pkgname"] != $pkg_name) {
					$error = __("Package names do not match.");
				}
			}
    }

    # TODO This is where other additional error checking can be
    # performed.  Examples: #md5sums == #sources?, md5sums of any
    # included files match?, install scriptlet file exists?
    #


    # Now, run through the pkgbuild array and do any $pkgname/$pkgver
    # substituions.
    #
    if (!$error) {
      $pkgname_var = $pkgbuild["pkgname"];
      $pkgver_var = $pkgbuild["pkgver"];
      $new_pkgbuild = array();
      while (list($k, $v) = each($pkgbuild)) {
        $v = str_replace("\$pkgname", $pkgname_var, $v);
        $v = str_replace("\$pkgver", $pkgver_var, $v);
        $new_pkgbuild[$k] = $v;
      }
    }

		# update the backend database
		#
    if (!$error) {
      $dbh = db_connect();
      if ($pkg_exists) {

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

        # $q = "INSERT INTO PackageUploadHistory ..."

      } else {
        # this is a brand new package
        #
        # TODO
        # $q = "INSERT ..."
      }
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
      $pkg_categories = pkgCategories();
      $pkg_locations = pkgLocations();

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
      print __("Package Category").":</td>\n";
      print "  <td span='f4' align='left'>";
      print "<select name='category'>";
      print "<option value='0'> " . __("Select Category") . "</option>";
      while (list($k, $v) = each($pkg_categories)) {
        print "<option value='".$k."'> " . $v . "</option>";
      }
      print "</select></td>\n";
      print "</tr>\n";
      print "<tr>\n";
      print "  <td span='f4' align='right'>";
      print __("Package Location").":</td>\n";
      print "  <td span='f4' align='left'>";
      print "<select name='location'>";
      print "<option value='0'> " . __("Select Location") . "</option>";
      while (list($k, $v) = each($pkg_locations)) {
        print "<option value='".$k."'> " . $v . "</option>";
      }
      print "</select></td>\n";
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
			print "<input type='radio' name='overwrite' value='1'> ".__("Yes");
			print "&nbsp;&nbsp;&nbsp;";
			print "<input type='radio' name='overwrite' value='0' checked> ";
			print __("No");
			print "  </td>\n";
			print "</tr>\n";
			print "<tr>\n";
			print "  <td valign='top' span='f4' align='right'>";
      print __("Comments").":</td>\n";
			print "  <td span='f4' align='left'>";
      print "<textarea rows='10' cols='50' name='comments'></textarea>";
			print "  </td>\n";
			print "</tr>\n";

			print "<tr>\n";
			print "  <td>&nbsp;</td>\n";
			print "  <td align='left'>";
			print "<input class='button' type='submit' value='".__("Upload")."' />\n";
      print "&nbsp;&nbsp;&nbsp;";
			print "<input class='button' type='reset' value='".__("Reset")."' />\n";
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
