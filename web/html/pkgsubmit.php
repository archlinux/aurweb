<?
include("aur.inc");         # access AUR common functions
include("submit_po.inc");   # use some form of this for i18n support
set_lang();                 # this sets up the visitor's language
check_sid();                # see if they're still logged in
html_header();              # print out the HTML header

# this is the directory that new packages will be uploaded to
#
$UPLOAD_DIR = "/tmp/aur/temp";

if ($_REQUEST["upload"]) {
	# try and process the upload
	#

} else {
	# give the visitor the default upload page
	#
	print "<center>\n";
	if (ini_get("file_uploads")) {
		print "<form action='/pkgsubmit.php' method='post'";
		print "	enctype='multipart/form-data'>\n";
		print "<input type='hidden' name='MAX_FILE_SIZE' value='";
		print initeger(ini_get("upload_max_filesize"))."' />\n";
		print "Upload package: ";
		print "<input type='file' name='pfile' size='30' />\n";
		print "&nbsp;&nbsp;&nbsp;&nbsp;";
		print "<input class='button' type='submit' value='Upload' />\n";
		print "</form>\n";
	} else {
		print "Sorry, uploads are not permitted by this server.\n<br />\n";
	}
	print "</center>\n";
}

html_footer("\$Id$");
?>
