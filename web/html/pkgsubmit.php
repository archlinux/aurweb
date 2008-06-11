<?php

include("config.inc");

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../lang');
require('Archive/Tar.php');
require('File/Find.php');

include("aur.inc");         # access AUR common functions
include("submit_po.inc");   # use some form of this for i18n support
include("pkgfuncs.inc");    # package functions

set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in
html_header("Submit");

?>

<div class="pgbox">
  <div class="pgboxtitle">
    <span class="f3"><?php print __("Submit"); ?></span>
  </div>
  <div class="pgboxbody">

<?php

if ($_COOKIE["AURSID"]) {
  
	# Track upload errors
	$error = "";

	if ($_REQUEST["pkgsubmit"]) {
	  
		# Before processing, make sure we even have a file
		if ($_FILES['pfile']['size'] == 0){
			$error = __("Error - No file uploaded");
		}

		# Temporary dir to put the tarball contents
		$tempdir = UPLOAD_DIR . uid_from_sid($_COOKIE['AURSID']) . time();

		if (!$error) {
			if (!@mkdir($tempdir)) {
				$error = __("Could not create incoming directory: %s.",
					array($tempdir));
			} else {
				if (!@chdir($tempdir)) {
					$error = __("Could not change directory to %s.",
						array($tempdir));
				} else {
				  if ($_FILES['pfile']['name'] == "PKGBUILD") {
				    move_uploaded_file($_FILES['pfile']['tmp_name'], $tempdir . "/PKGBUILD");
				  } else {
  					$tar = new Archive_Tar($_FILES['pfile']['tmp_name']);
  					$extract = $tar->extract();
  					
  					if (!$extract) {
  						$error = __("Unknown file format for uploaded file.");
  					}
				  }
				}
			}
		}

		# Find the PKGBUILD
		if (!$error) {
		  $pkgbuild = File_Find::search('PKGBUILD', $tempdir);
		  
		  if (count($pkgbuild) > 0) {
		    $pkgbuild = $pkgbuild[0];
		    $pkg_dir = dirname($pkgbuild);
		  } else {
		    $error = __("Error trying to unpack upload - PKGBUILD does not exist.");
		  }
		}

		# if no error, get list of directory contents and process PKGBUILD
		#
		if (!$error) {
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
				$char_counts = count_chars($line, 0);
				if (substr($line, strlen($line)-1) == "\\") {
					# continue appending onto existing line_no
					#
					$current_line .= substr($line, 0, strlen($line)-1);
					$continuation_line = 1;
				} elseif ($char_counts[ord('(')] > $char_counts[ord(')')]) {
					# assumed continuation
					# continue appending onto existing line_no
					#
					$current_line .= $line . " ";
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
			# 'pkgbuild' array.	Also check to make sure it has the build()
			# function.
			#
			$seen_build_function = 0;
			while (list($k, $line) = each($lines)) {
				$lparts = explode("=", $line, 2);
				if (count($lparts) == 2) {
					# this is a variable/value pair, strip out
					# array parens and any quoting, except in pkgdesc
					# for pkgdesc, only remove start/end pairs of " or '
					if ($lparts[0]=="pkgdesc") {
						if ($lparts[1]{0} == '"' && 
								$lparts[1]{strlen($lparts[1])-1} == '"') {
							$pkgbuild[$lparts[0]] = substr($lparts[1], 1, -1);
						}
					 	elseif 
							($lparts[1]{0} == "'" && 
							 $lparts[1]{strlen($lparts[1])-1} == "'") {
							$pkgbuild[$lparts[0]] = substr($lparts[1], 1, -1);
						} else { 
							$pkgbuild[$lparts[0]] = $lparts[1];
					 	}
					} else {
						$pkgbuild[$lparts[0]] = str_replace(array("(",")","\"","'"), "",
								$lparts[1]);
					}
				} else {
					# either a comment, blank line, continued line, or build function
					#
					if (substr($lparts[0], 0, 5) == "build") {
						$seen_build_function = 1;
					}
				}
				# XXX: closes bug #2280?  Might as well let the loop complete rather
				# than break after the build() function.
				#
				#if ($seen_build_function) {break;}
			}

			# some error checking on PKGBUILD contents - just make sure each
			# variable has a value.	This does not do any validity checking
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
			if (!array_key_exists("license", $pkgbuild)) {
					$error = __("Missing license variable in PKGBUILD.");
			}            
			if (!array_key_exists("pkgrel", $pkgbuild)) {
				$error = __("Missing pkgrel variable in PKGBUILD.");
			}
			if (!array_key_exists("pkgver", $pkgbuild)) {
				$error = __("Missing pkgver variable in PKGBUILD.");
			}
			if (!array_key_exists("arch", $pkgbuild)) {
					$error = __("Missing arch variable in PKGBUILD.");
			}
			if (!array_key_exists("pkgname", $pkgbuild)) {
				$error = __("Missing pkgname variable in PKGBUILD.");
			}
		}

		# TODO This is where other additional error checking can be
		# performed.	Examples: #md5sums == #sources?, md5sums of any
		# included files match?, install scriptlet file exists?
		#
		
		# Check for http:// or other protocol in url
		# 
		if (!$error) {
			$parsed_url = parse_url($pkgbuild['url']);
			if (!$parsed_url['scheme']) {
				$error = __("Package URL is missing a protocol (ie. http:// ,ftp://)");
			}
		}
			
		# Now, run through the pkgbuild array and do any $pkgname/$pkgver
		# substituions.
		#
		#TODO: run through and do ALL substitutions, to cover custom vars
		if (!$error) {
			$pkgname_var = $pkgbuild["pkgname"];
			$pkgver_var = $pkgbuild["pkgver"];
			$new_pkgbuild = array();
			while (list($k, $v) = each($pkgbuild)) {
				$v = str_replace('$pkgname', $pkgname_var, $v);
				$v = str_replace('${pkgname}', $pkgname_var, $v);
				$v = str_replace('$pkgver', $pkgver_var, $v);
				$v = str_replace('${pkgver}', $pkgver_var, $v);
				$new_pkgbuild[$k] = $v;
			}
		}

		# now we've parsed the pkgbuild, let's move it to where it belongs
		#
		if (!$error) {
			$pkg_name = str_replace("'", "", $pkgbuild['pkgname']);
			$pkg_name = escapeshellarg($pkg_name);
			$pkg_name = str_replace("'", "", $pkg_name); # get rid of single quotes
            
			# Solves the problem when you try to submit PKGBUILD
			# that have the name with a period like (gstreamer0.10)
			# Added support for packages with + characters like (mysql++).
			$presult = preg_match("/^[a-z0-9][a-z0-9\.+_-]*$/", $pkg_name);
			
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
			if (can_submit_pkg($pkg_name, $_COOKIE["AURSID"])) {
				if (file_exists(INCOMING_DIR . $pkg_name)) {
					# blow away the existing file/dir and contents
					#
					rm_rf(INCOMING_DIR . $pkg_name);
				}

				if (!@mkdir(INCOMING_DIR.$pkg_name)) {
					$error = __("Could not create directory %s.",
						array(INCOMING_DIR.$pkg_name));
				}

        rename($pkg_dir, INCOMING_DIR . $pkg_name . "/" . $pkg_name);
			} else {
				$error = __("You are not allowed to overwrite the %h%s%h package.",
					array("<b>", $pkg_name, "</b>"));
			}
		}

		# Re-tar the package for consistency's sake
		#
		if (!$error) {
			if (!@chdir(INCOMING_DIR.$pkg_name)) {
				$error = __("Could not change directory to %s.",
					array(INCOMING_DIR.$pkg_name));
			}
		}
		
		if (!$error) {
		  $tar = new Archive_Tar($pkg_name . '.tar.gz');
		  $create = $tar->create(array($pkg_name));
		  
			if (!$create) {
				$error = __("Could not re-tar");
			}
		}
		
		# whether it failed or not we can clean this out
		if (file_exists($tempdir)) {
			rm_rf($tempdir);
		}

		# update the backend database
		#
		if (!$error) {
			$dbh = db_connect();
			# this is an overwrite of an existing package, the database ID
			# needs to be preserved so that any votes are retained.	However,
			# PackageDepends, PackageSources, and PackageContents can be
			# purged.
			#
			$q = "SELECT * FROM Packages ";
			$q.= "WHERE Name = '".mysql_real_escape_string($new_pkgbuild['pkgname'])."'";
			$result = db_query($q, $dbh);
			$pdata = mysql_fetch_assoc($result);

			if ($pdata) {

				# flush out old data that will be replaced with new data
				#
				$q = "DELETE FROM PackageDepends WHERE PackageID = ".$pdata["ID"];
				db_query($q, $dbh);
				$q = "DELETE FROM PackageSources WHERE PackageID = ".$pdata["ID"];
				db_query($q, $dbh);

				# update package data
				#
				$q = "UPDATE Packages SET ";
				# if the package was a dummy, undummy it and change submitter
				# also give it a maintainer so we dont go making an orphan
				if ($pdata['DummyPkg'] == 1) {
					$q.= "DummyPkg = 0, ";
					$q.= "SubmitterUID = ".uid_from_sid($_COOKIE["AURSID"]).", ";
					$q.= "MaintainerUID = ".uid_from_sid($_COOKIE["AURSID"]).", ";
					$q.= "SubmittedTS = UNIX_TIMESTAMP(), ";
				} else {
					$q.="ModifiedTS = UNIX_TIMESTAMP(), ";
				}
				$q.="Name='".mysql_real_escape_string($new_pkgbuild['pkgname'])."', ";
				$q.="Version='".mysql_real_escape_string($new_pkgbuild['pkgver'])."-".
				  mysql_real_escape_string($new_pkgbuild['pkgrel'])."',";
				if ($_POST['category'] > 1) {
				$q.="CategoryID=".mysql_real_escape_string($_REQUEST['category']).", ";
			}
                $q.="License='".mysql_real_escape_string($new_pkgbuild['license'])."', ";
                $q.="Description='".mysql_real_escape_string($new_pkgbuild['pkgdesc'])."', ";
				$q.="URL='".mysql_real_escape_string($new_pkgbuild['url'])."', ";
				$q.="LocationID=2, ";
				$fspath=INCOMING_DIR.$pkg_name."/".$pkg_name.".tar.gz";
				$q.="FSPath='".mysql_real_escape_string($fspath)."', ";
				$urlpath=URL_DIR.$pkg_name."/".$pkg_name.".tar.gz";
				$q.="OutOfDate=0, ";
				$q.="URLPath='".mysql_real_escape_string($urlpath)."' ";
				$q.="WHERE ID = " . $pdata["ID"];
				$result = db_query($q, $dbh);

				# update package depends
				#
				$depends = explode(" ", $new_pkgbuild['depends']);
                
        while (list($k, $v) = each($depends)) {
					$q = "INSERT INTO PackageDepends (PackageID, DepPkgID, DepCondition) VALUES (";
					$deppkgname = preg_replace("/[<>]?=.*/", "", $v);
          $depcondition = str_replace($deppkgname, "", $v);
                    
          # Solve the problem with comments and deps
          # added by: dsa <dsandrade@gmail.com>
          if ($deppkgname == "#") { break; }
                    
					$deppkgid = create_dummy($deppkgname, $_COOKIE['AURSID']);
					
          if(!empty($depcondition)) {
              $q .= $pdata["ID"].", ".$deppkgid.", '".$depcondition."')";
          } else {
              $q .= $pdata["ID"].", ".$deppkgid.", '')";
          }
                        
					db_query($q, $dbh);
				}

				# Insert sources, if they don't exist don't inser them
				# 
				if ($new_pkgbuild['source'] != "") {
					$sources = explode(" ", $new_pkgbuild['source']);
					while (list($k, $v) = each($sources)) {
						$q = "INSERT INTO PackageSources (PackageID, Source) VALUES (";
						$q .= $pdata["ID"].", '".mysql_real_escape_string($v)."')";
						db_query($q, $dbh);
					}
				}
			} else {
				# this is a brand new package
				#
				$q = "INSERT INTO Packages ";
				$q.= " (Name, License, Version, CategoryID, Description, URL, LocationID, ";
				$q.= " SubmittedTS, SubmitterUID, MaintainerUID, FSPath, URLPath) ";
				$q.= "VALUES ('";
				$q.= mysql_real_escape_string($new_pkgbuild['pkgname'])."', '";
                $q.= mysql_real_escape_string($new_pkgbuild['license'])."', '";
				$q.= mysql_real_escape_string($new_pkgbuild['pkgver'])."-".
				  mysql_real_escape_string($new_pkgbuild['pkgrel'])."', ";
				$q.= mysql_real_escape_string($_REQUEST['category']).", '";
				$q.= mysql_real_escape_string($new_pkgbuild['pkgdesc'])."', '";
				$q.= mysql_real_escape_string($new_pkgbuild['url']);
				$q.= "', 2, ";
				$q.= "UNIX_TIMESTAMP(), ";
				$q.= uid_from_sid($_COOKIE["AURSID"]).", ";
				$q.= uid_from_sid($_COOKIE["AURSID"]).", '";
				$fspath=INCOMING_DIR.$pkg_name."/".$pkg_name.".tar.gz";
				$q.= mysql_real_escape_string($fspath)."', '";
				$urlpath=URL_DIR.$pkg_name."/".$pkg_name.".tar.gz";
				$q.= mysql_real_escape_string($urlpath)."')";
				$result = db_query($q, $dbh);
#				print $result . "<br>";

				$packageID = mysql_insert_id($dbh);

				# update package depends
				#
				$depends = explode(" ", $new_pkgbuild['depends']);
				while (list($k, $v) = each($depends)) {
					$q = "INSERT INTO PackageDepends (PackageID, DepPkgID, DepCondition) VALUES (";
					$deppkgname = preg_replace("/[<>]?=.*/", "", $v);
					$depcondition = str_replace($deppkgname, "", $v);
                    
          # Solve the problem with comments and deps
          # added by: dsa <dsandrade@gmail.com>
          if ($deppkgname == "#") { break; }
          
          $deppkgid = create_dummy($deppkgname, $_COOKIE['AURSID']);
          
          if(!empty($depcondition)) {
              $q .= $packageID.", ".$deppkgid.", '".$depcondition."')";
          } else {
              $q .= $packageID.", ".$deppkgid.", '')";
          }
          
					db_query($q, $dbh);
				}

				# insert sources
				#
				if ($new_pkgbuild['source'] != "") {
					$sources = explode(" ", $new_pkgbuild['source']);
					while (list($k, $v) = each($sources)) {
						$q = "INSERT INTO PackageSources (PackageID, Source) VALUES (";
						$q .= $packageID.", '".mysql_real_escape_string($v)."')";
						db_query($q, $dbh);
					}
				}
			}
		}

		# must chdir because include dirs are relative!
		chdir($_SERVER['DOCUMENT_ROOT']);
	}


	if (!$_REQUEST["pkgsubmit"] || $error) {
		# User is not uploading, or there were errors uploading - then
		# give the visitor the default upload form
		#
		if (ini_get("file_uploads")) {
			if ($error) {
				print "<span class='error'>".$error."</span><br />\n";
				print "<br />\n";
			}
            
			if ($warning) {
					print "<br><span class='error'>".$warning."</span><br />\n";
					print "<br />\n";
			}
            
			$pkg_categories = pkgCategories();
			$pkg_locations = pkgLocations();
?>

<form action='/pkgsubmit.php' method='post' enctype='multipart/form-data'>
	<input type='hidden' name='pkgsubmit' value='1' />
	<table border='0' cellspacing='5'>
		<tr>
			<td span='f4' align='right'><?php print __("Package Category"); ?>:</td>
			<td span='f4' align='left'>
			<select name='category'>
				<option value='1'><?php print __("Select Category"); ?></option>
				<?php
					while (list($k, $v) = each($pkg_categories)) {
						print "<option value='".$k."'";
						if (isset($_POST['category']) && $_POST['category'] == $k) {
							print " selected='selected'";
						}
						print "> " . $v . "</option>";
					}
				?>
			</select>
			</td>
		</tr>
		<tr>
			<td span='f4' align='right'><?php print __("Upload package file"); ?>:</td>
			<td span='f4' align='left'>
				<input type='file' name='pfile' size='30' />
			</td>
		</tr>
		<tr>
			<td align='left'>
				<input class='button' type='submit' value='<?php print __("Upload"); ?>' />
			</td>
		</tr>
	</table>
</form>

<?php
		} else {
			print __("Sorry, uploads are not permitted by this server.");
			print "<br />\n";
		}
	} else {
		print __("Package upload successful.");
        
        if ($warning) {
            print "<span class='warning'>".$warning."</span><br />\n";
            print "<br />\n";
        }
	}

} else {
	# visitor is not logged in
	#
	print __("You must create an account before you can upload packages.");
	print "<br />\n";
}

?>

  </div>
</div>

<?php

html_footer(AUR_VERSION);
# vim: ts=2 sw=2 noet ft=php

?>
