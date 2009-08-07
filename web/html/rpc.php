<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aurjson.class.php");

if ( $_SERVER['REQUEST_METHOD'] == 'GET' ) {
    if ( isset($_GET['type']) ) {
        $rpc_o = new AurJSON();
        echo $rpc_o->handle($_GET);
    }
    else {
        // dump a simple usage output for people to use.
        // this could be moved to an api doc in the future, or generated from 
        // the AurJSON class directly with phpdoc. For now though, just putting it here.
        echo '<html><body>';
        echo 'The methods currently allowed are: <br />';
        echo '<ul>';
        echo '<li>search</li>';
        echo '<li>info</li>';
        echo '</ul><br />';
        echo 'Each method requires the following HTTP GET syntax:<br />';
        echo '&nbsp;&nbsp; type=<i>methodname</i>&arg=<i>data</i> <br /><br />';
        echo 'Where <i>methodname</i> is the name of an allowed method, and <i>data</i> is the argument to the call.<br />';
        echo '<br />';
        echo 'If you need jsonp type callback specification, you can provide an additional variable <i>callback</i>.<br />';
        echo 'Example URL: <br />&nbsp;&nbsp; http://aur-url/rpc.php?type=search&arg=foobar&callback=jsonp1192244621103';
        echo '</body></html>';
    }
}
else {
    echo 'POST NOT SUPPORTED';
}
?>
