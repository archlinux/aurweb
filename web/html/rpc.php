<?php
set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');
include_once("aurjson.class.php");

if ( $_SERVER['REQUEST_METHOD'] != 'GET' ) {
	header('HTTP/1.1 405 Method Not Allowed');
	exit();
}

if ( isset($_GET['type']) ) {
	$rpc_o = new AurJSON();
	echo $rpc_o->handle($_GET);
}
else {
	echo file_get_contents('../../doc/rpc.html');
}
?>
