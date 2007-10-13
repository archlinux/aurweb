<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../lang');

include("aur.inc");
include("aurjson.class.php");

$rpc_o = new AurJSON();
if ( $_SERVER['REQUEST_METHOD'] == 'GET' ) {
    if ( isset($_GET['type']) ) {
        echo $rpc_o->handle($_GET);
    }
    else {
        echo '<html><body>';
        echo $rpc_o->usage();
        echo '</body></html>';
    }
}
else {
    echo 'POST NOT SUPPORTED';
}
?>
