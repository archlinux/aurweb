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

		# first, see if this package already exists, and if it can be overwritten
	 	#	
		if (package_exists($_FILES["pfile"]["name"])) { # TODO write function
			# ok, it exists - should it be overwritten, and does the user have
			# the permissions to do so?
			#
			# TODO write 'can_overwrite_pkg' function
			if (can_overwrite_pkg($_FILES["pfile"]["name"], $_COOKIE["AURSID"])) {
				if (!$_REQUEST["overwrite"]) {
					$error = __("You did not tag the 'overwrite' checkbox.");
				}
			} else {
				$error = __("You are not allowed to overwrite the %h%s%h package.",
						array("<b>", $_FILES["pfile"]["name"], "</b>"));
			}
		}

		if (!$error)) {
			# no errors checking upload permissions, go ahead and try to process
			# the uploaded package file.
			#

			$upload_file = $UPLOAD_DIR . $_FILES["pfile"]["name"];
			if (move_uploaded_file($_FILES["pfile"]["tmp_name"], $upload_file)) {
				# ok, we can proceed
				#
				if (file_exists($INCOMING_DIR . $_FILES["pfile"]["name"])) {
					# blow away the existing file/dir and contents
					#
					rm_rf($INCOMING_DIR . $_FILES["pfile"]["name"]);
				}

			} else {
				# errors uploading file...
				#
				$error = __("Error trying to upload file - please try again.");
			}
		}

	}


	if (!$_REQUEST["pkgsubmit"] || !$error)) {
		# give the visitor the default upload form
		#
		if (ini_get("file_uploads")) {
			if (!$error) {
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
			print __("Upload package").":</td>\n";
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
			print "  <td align='center' colspan='2'>&nbsp;</td>\n";
			print "</tr>\n";

			print "<tr>\n";
			print "  <td align='right'>";
			print "<input class='button' type='submit' value='".__("Upload")."' />\n";
			print "</td>\n";
			print "  <td>&nbsp;</td>\n";
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
?>
