<?php

function config_get($section, $key) {
	global $AUR_CONFIG;

	if (!isset($AUR_CONFIG)) {
		$AUR_CONFIG = parse_ini_file("../../conf/config", true);
	}

	return $AUR_CONFIG[$section][$key];
}

function config_get_int($section, $key) {
	return intval(config_get($section, $key));
}

function config_get_bool($section, $key) {
	$val = strtolower(config_get($section, $key));
	return ($val == 'yes' || $val == 'true' || $val == '1');
}
