<?
# common header
#
function html_header() {
	print "<html>\n";
	print "<head>\n";
	print "<title>AUR</title>\n";
	print "<link rel='stylesheet' type='text/css' href='/css/fonts.css'/>\n";
	print "<link rel='stylesheet' type='text/css' href='/css/containers.css'/>\n";
	print "<link rel='shortcut icon' href='/images/favicon.ico'/>\n";
	print "</head>\n";
	print "<body bgcolor='white'>\n";
	print "<table cellspacing='0' ";
	print "style='background-color: #000; width: 100%;'>\n";
	print "    <tr>\n";
	print "        <td class='preHeader'><span class='preHeader'>AUR: An ";
	print "ArchLinux project</span></td>\n";
	print "    </tr>\n";
	print "    <tr>\n";
	print "        <td class='headerFill'>\n";
	print "            <table width='100%'>\n";
	print "            <tr>\n";
	print "                <td class='headerDisplay'><a href='";
	print $_SERVER['PHP_SELF']."'>";
	print "<img src='/images/AUR-logo-80.png' border='0'></a></td>\n";
	print "                <td class='headerDisplay' valign='top' align='right'>";
	print "<span class='fix'>ArchLinux User-community Repository</span></td>\n";
	print "            </tr>\n";
	print "            </table>\n";
	print "    </tr>\n";
	print "</table>\n";
	print "<!-- Start of main content -->\n\n";

	return;
}

# common footer
#
function html_footer($ver="") {
	print "\n\n<!-- End of main content -->";
	print "<p>\n";
	if ($ver) {
		print "<table border='0' cellpadding='0' cellspacing='0' width='100%'>\n";
		print "<tr><td align='right'><span class='fix'>".$ver."</span></td></tr>\n";
		print "</table>\n";
	}
	print "</body>\n</html>";
	return;
}

# vim: ts=2 sw=2 noet ft=php
?>
