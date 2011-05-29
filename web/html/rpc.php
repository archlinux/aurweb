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
	// dump a simple usage output for people to use.
	// this could be moved to an api doc in the future, or generated from
	// the AurJSON class directly with phpdoc. For now though, just putting it
	// here.
?>
<html><body>
<p>The methods currently allowed are:</p>
<ul>
  <li><tt>search</tt></li>
  <li><tt>info</tt></li>
  <li><tt>multiinfo</tt></li>
  <li><tt>msearch</tt></li>
</ul>
<p>Each method requires the following HTTP GET syntax:</p>
<pre>type=<em>methodname</em>&amp;arg=<em>data</em></pre>
<p>Where <em>methodname</em> is the name of an allowed method, and <em>data</em> is the argument to the call.</p>
<p>If you need jsonp type callback specification, you can provide an additional variable <em>callback</em>.</p>
<p>Example URL: <tt>http://aur-url/rpc.php?type=search&amp;arg=foobar&amp;callback=jsonp1192244621103</tt></p>
</body></html>
<?php
// close if statement
}
?>
