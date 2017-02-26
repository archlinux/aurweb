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

include_once("confparser.inc.php");
include_once('DB.class.php');
include_once('gettext.php');
include_once('streams.php');

global $streamer, $l10n;

# Languages we have translations for
$SUPPORTED_LANGS = array(
	"ar" => "العربية",
	"ast" => "Asturianu",
	"ca" => "Català",
	"cs" => "Český",
	"da" => "Dansk",
	"de" => "Deutsch",
	"en" => "English",
	"el" => "Ελληνικά",
	"es" => "Español",
	"es_419" => "Español (Latinoamérica)",
	"fi" => "Finnish",
	"fr" => "Français",
	"he" => "עברית",
	"hr" => "Hrvatski",
	"hu" => "Magyar",
	"it" => "Italiano",
	"ja" => "日本語",
	"nb" => "Norsk",
	"nl" => "Nederlands",
	"pl" => "Polski",
	"pt_BR" => "Português (Brasil)",
	"pt_PT" => "Português (Portugal)",
	"ro" => "Română",
	"ru" => "Русский",
	"sk" => "Slovenčina",
	"sr" => "Srpski",
	"tr" => "Türkçe",
	"uk" => "Українська",
	"zh_CN" => "简体中文",
	"zh_TW" => "正體中文"
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

function _n($msgid1, $msgid2, $n) {
	global $l10n;

	$translated = sprintf($l10n->ngettext($msgid1, $msgid2, $n), $n);
	return htmlspecialchars($translated, ENT_QUOTES);
}

# set up the visitor's language
#
function set_lang() {
	global $LANG;
	global $SUPPORTED_LANGS;
	global $streamer, $l10n;

	$update_cookie = 0;
	if (isset($_POST['setlang'])) {
		# visitor is requesting a language change
		#
		$LANG = $_POST['setlang'];
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
		$q.= "AND Sessions.SessionID = ";
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
		$LANG = config_get('options', 'default_lang');
	}

	if ($update_cookie) {
		$timeout = intval(config_get('options', 'persistent_cookie_timeout'));
		$cookie_time = time() + $timeout;
		setcookie("AURLANG", $LANG, $cookie_time, "/");
	}

	$streamer = new FileReader('../locale/' . $LANG .
		'/LC_MESSAGES/aur.mo');
	$l10n = new gettext_reader($streamer, true);

	return;
}

