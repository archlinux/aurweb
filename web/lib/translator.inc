<?php
set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../lang');

# this include file provides support for i18n
#

# usage:
#   use the __() function for returning translated strings of
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
#	print __("%s has %s apples.", "Bill", "5");
#	print __("This is a %h%s%h problem!", "<b>","major","</b>");
#
# deprecated usage:
#	print __("%s has %s apples.", array("Bill", "5"));

include_once('config.inc');

global $_t;

function include_lang($trans) {
	global $LANG;

	if ($LANG != DEFAULT_LANG) {
		return include_once("$LANG/$trans");
	}
	else
		return true;
}

function __() {
	global $_t;
	global $LANG;

	# create the translation, if it doesn't exist, highlight it
	#
	$args = func_get_args();

	# First argument is always string to be translated
	$tag = $args[0];

	if (empty($LANG) || $LANG == DEFAULT_LANG)
		$translated = $tag;
	else
		$translated = $_t[$tag];

	# If there is no translation, just print the given string.
	if (empty($translated)) {
		$translated = $tag;
	}

	$translated = htmlspecialchars($translated, ENT_QUOTES); 

	# This condition is to reorganise the arguments in case of
	# deprecated usage. __("string", array("string","string"))
	if (!empty($args[1]) && is_array($args[1])) {
		array_unshift($args[1], $tag);
		$args = $args[1];
	}

	$num_args = sizeof($args);

	# Subsequent arguments are strings to be formatted
	if ( $num_args > 1 ) {
		for ($i = 1; $i < $num_args; $i++) {
			$translated = preg_replace("/\%[sh]/", $args[$i], $translated, 1);
		}
	}

	return $translated;
}

