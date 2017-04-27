<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
include_once("pkgbasefuncs.inc.php");

if (!isset($base_id)) {
	header('Location: /');
	exit();
}

html_header(__("Flag Comment"));
$message = pkgbase_get_flag_comment($base_id);
include('flag_comment.php');
html_footer(AURWEB_VERSION);
