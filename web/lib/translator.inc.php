<?php
set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../lang');

# This file provides support for i18n

# usage:
#   use the __() function for returning translated strings of
#   text.  The string can contain escape codes %h for HTML
#   and %s for regular text.
#
# examples:
#	print __("%s has %s apples.", "Bill", "5");
#	print __("This is a %hmajor%h problem!", "<b>", "</b>");

include_once('config.inc.php');
include_once('gettext.php');
include_once('streams.php');

global $streamer, $l10n;

function __() {
	global $LANG;
	global $l10n;

	# Create the translation.
	$args = func_get_args();

	# First argument is always string to be translated
	$tag = $args[0];

	# Translate using gettext_reader initialized before.
	$translated = $l10n->translate($tag);
	$translated = htmlspecialchars($translated, ENT_QUOTES);

	$num_args = sizeof($args);

	# Subsequent arguments are strings to be formatted
	#
	# TODO: make this more robust.
	# '%%' should translate to a literal '%'

	if ( $num_args > 1 ) {
		for ($i = 1; $i < $num_args; $i++) {
			$translated = preg_replace("/\%[sh]/", $args[$i], $translated, 1);
		}
	}

	return $translated;
}

