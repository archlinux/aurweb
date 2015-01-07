<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
include_once("pkgbasefuncs.inc.php");

set_lang();
check_sid();

if (!isset($base_id) || !has_credential(CRED_PKGBASE_EDIT_COMAINTAINERS, array(pkgbase_maintainer_uid($base_id)))) {
	header('Location: /');
	exit();
}

html_header(__("Manage Co-maintainers"));
$users = pkgbase_get_comaintainers($base_id);
include('comaintainers_form.php');
html_footer(AUR_VERSION);


