<?
# this include file provides support for i18n
#

# usage:
#   use the _() function for returning translated strings of
#   text.  The string can contain escape codes %h for HTML
#   and %s for regular text.
#
# supporting scripts:
#   there is a supporting script, web/utils/genpopo, that will
#   parse the PHP files and create PHP include files that contain
#   a mapping for each translated language.  The include files
#   have the form,
#
#     $_t["en"]["My cat is large."] = "My cat is large.";
#     $_t["es"]["My cat is large."] = "Mi gato esta grande.";
#
# examples:
#   print _("%s has %s apples.", array("Bill", "5"));
#   print _("This is a %h%s%h problem!", array("<b>","major","</b>"));

include_once("common_po.inc");

function _($tag, $args=array()) {
	global $_t;
	global $LANG;

	# default to English if the lang hasn't been provided
	#
	if (!$LANG) {
		$lang = "en";
	} else {
		$lang = $LANG;
	}

	# create the translation, if it doesn't exist, highlight it
	#
	$translated = $_t[$lang][$tag];
	if (!$translated) {
		$translated = "<blink><b>_" . $tag . "_</b></blink>";
	}

	# replace escape substitutions
	#
	if (!empty($args)) {
		while (list($k, $v) = each($args)) {
			$translated = preg_replace("/\%[sh]/", $v, $translated, 1);
		}
	}
	return $translated;
}

# vim: ts=2 sw=2 noet ft=php
?>
