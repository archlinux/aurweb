<?php
/**
 * Provide some variable Prometheus metrics. A new requests.route type
 * gets created for each request made and we keep a count using our
 * existing Memcached or APC configurable cache, with route
 * = {request_uri}?{query_string}.
 *
 * TL;DR -- The 'requests' counter is used to give variable requests
 * based on their request_uris and query_strings.
 **/
include_once('metricfuncs.inc.php');

// Render metrics based on options.cache storage.
render_metrics();

?>
