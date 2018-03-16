<?php

function config_load() {
	global $AUR_CONFIG;

	if (!isset($AUR_CONFIG)) {
		$path = getenv('AUR_CONFIG');
		if (!$path) {
			$path = "/etc/aurweb/config";
		}
		if (file_exists($path)) {
			$AUR_CONFIG = parse_ini_file($path, true, INI_SCANNER_RAW);
		} else {
			die("aurweb config file not found");
		}
	}
}

function config_get($section, $key) {
	global $AUR_CONFIG;
	config_load();

	return $AUR_CONFIG[$section][$key];
}

function config_get_int($section, $key) {
	return intval(config_get($section, $key));
}

function config_get_bool($section, $key) {
	$val = strtolower(config_get($section, $key));
	return ($val == 'yes' || $val == 'true' || $val == '1');
}

function config_items($section) {
	global $AUR_CONFIG;
	config_load();

	return $AUR_CONFIG[$section];
}

function config_section_exists($key) {
	global $AUR_CONFIG;
	config_load();

	return array_key_exists($key, $AUR_CONFIG);
}
