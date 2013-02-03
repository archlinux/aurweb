<?php
set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../lang');

# This file provides support for i18n

# usage:
#   use the __() function for returning translated strings of
#   text.  The string can contain escape codes "%s".
#
# examples:
#	print __("%s has %s apples.", "Bill", "5");
#	print __("This is a %smajor%s problem!", "<strong>", "</strong>");

include_once('config.inc.php');
include_once('DB.class.php');
include_once('gettext.php');
include_once('streams.php');

global $streamer, $l10n;

# Languages we have translations for
$SUPPORTED_LANGS = array(
	"ca" => "Català",
	"cs" => "česky",
	"da" => "Dansk",
	"de" => "Deutsch",
	"en" => "English",
	"el" => "Ελληνικά",
	"es" => "Español",
	"fi" => "Finnish",
	"fr" => "Français",
	"he" => "עברית",
	"hr" => "Hrvatski",
	"hu" => "Magyar",
	"it" => "Italiano",
	"nb" => "Norsk",
	"nl" => "Nederlands",
	"pl" => "Polski",
	"pt_BR" => "Português (Brasil)",
	"pt_PT" => "Português (Portugal)",
	"ro" => "Română",
	"ru" => "Русский",
	"sr" => "Srpski",
	"tr" => "Türkçe",
	"uk" => "Українська",
	"zh_CN" => "简体中文"
);

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

# set up the visitor's language
#
function set_lang() {
	global $LANG;
	global $SUPPORTED_LANGS;
	global $PERSISTENT_COOKIE_TIMEOUT;
	global $streamer, $l10n;

	$update_cookie = 0;
	if (isset($_REQUEST['setlang'])) {
		# visitor is requesting a language change
		#
		$LANG = $_REQUEST['setlang'];
		$update_cookie = 1;

	} elseif (isset($_COOKIE['AURLANG'])) {
		# If a cookie is set, use that
		#
		$LANG = $_COOKIE['AURLANG'];

	} elseif (isset($_COOKIE["AURSID"])) {
		# No language but a session; use default lang preference
		#
		$dbh = DB::connect();
		$q = "SELECT LangPreference FROM Users, Sessions ";
		$q.= "WHERE Users.ID = Sessions.UsersID ";
		$q.= "AND Sessions.SessionID = '";
		$q.= $dbh->quote($_COOKIE["AURSID"]);
		$result = $dbh->query($q);

		if ($result) {
			$row = $result->fetchAll();
			$LANG = $row[0];
		}
		$update_cookie = 1;
	}

	# Set $LANG to default if nothing is valid.
	if (!array_key_exists($LANG, $SUPPORTED_LANGS)) {
		$LANG = DEFAULT_LANG;
	}

	if ($update_cookie) {
		$cookie_time = time() + $PERSISTENT_COOKIE_TIMEOUT;
		setcookie("AURLANG", $LANG, $cookie_time, "/");
	}

	$streamer = new FileReader('../locale/' . $LANG .
		'/LC_MESSAGES/aur.mo');
	$l10n = new gettext_reader($streamer, true);

	return;
}

