<?php
set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../lang');

# This file provides support for i18n

# usage:
#   use the __() function for returning translated strings of
#   text.  The string can contain escape codes "%s".
#
# examples:
#	print __("%s has %s apples.", "Bill", "5");
#	print __("This is a %smajor%s problem!", "<b>", "</b>");

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
	$tag = array_shift($args);

	# Translate using gettext_reader initialized before.
	$translated = $l10n->translate($tag);
	$translated = htmlspecialchars($translated, ENT_QUOTES);

	# Subsequent arguments are strings to be formatted
	if (count($args) > 0) {
		$translated = vsprintf($translated, $args);
	}

	return $translated;
}

