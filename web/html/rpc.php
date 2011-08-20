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
<h2>Allowed methods</h2>
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
<h2>Examples</h2>
<dl>
  <dt><tt>search</tt></dt><dd><tt>http://aur-url/rpc.php?type=search&amp;arg=foobar</tt></li></dd>
  <dt><tt>info</tt></dt><dd><tt>http://aur-url/rpc.php?type=info&amp;arg=foobar</tt></dd>
  <dt><tt>multiinfo</tt></dt><dd><tt>http://aur-url/rpc.php?type=multiinfo&amp;arg[]=foo&amp;arg[]=bar</tt></dd>
  <dt><tt>msearch</tt></dt><dd><tt>http://aur-url/rpc.php?type=msearch&amp;arg=john</tt></li></dd>
  <dt>Callback</dt><dd><tt>http://aur-url/rpc.php?type=search&amp;arg=foobar&amp;callback=jsonp1192244621103</tt></dd>
</dl>
</body></html>
<?php
// close if statement
}
?>
