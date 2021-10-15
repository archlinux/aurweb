<?php
set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

require __DIR__ . '/../../vendor/autoload.php';
include_once("cachefuncs.inc.php");

use \Prometheus\Storage\InMemory;
use \Prometheus\CollectorRegistry;
use \Prometheus\RenderTextFormat;

// We always pass through an InMemory cache. This means that
// metrics are only good while the php-fpm service is running
// and will start again at 0 if it's restarted.
$registry = new CollectorRegistry(new InMemory());

function add_metric($anchor, $method, $path, $type = null) {

	global $registry;
	// We keep track of which routes we're interested in by storing
	// a JSON-encoded list into the "prometheus_metrics" key,
	// with each item being a JSON-encoded associative array
	// in the form: {'path': <route>, 'query_string': <query_string>}.
	$metrics = get_cache_value("prometheus_metrics");
	$metrics = $metrics ? json_decode($metrics) : array();

	$key = "$path:$type";

	// If the current request $path isn't yet in $metrics create
	// a new assoc array for it and push it into $metrics.
	if (!in_array($key, $metrics)) {
		$data = array(
			'anchor' => $anchor,
			'method' => $method,
			'path' => $path,
			'type' => $type
		);
		array_push($metrics, json_encode($data));
	}

	// Cache-wise, we also store the count values of each route
	// through the "prometheus:<route>" key. Grab the cache value
	// representing the current $path we're on (defaulted to 1).
	$count = get_cache_value("prometheus:$key");
	$count = $count ? $count + 1 : 1;

	$labels = ["method", "route"];
	if ($type)
		array_push($labels, "type");

	$gauge = $registry->getOrRegisterGauge(
		'aurweb',
		$anchor,
		'A metric count for the aurweb platform.',
		$labels
	);

	$label_values = [$data['method'], $data['path']];
	if ($type)
		array_push($label_values, $type);

	$gauge->set($count, $label_values);

	// Update cache values.
	set_cache_value("prometheus:$key", $count, 0);
	set_cache_value("prometheus_metrics", json_encode($metrics), 0);

}

function render_metrics() {
	if (!defined('EXTENSION_LOADED_APC') && !defined('EXTENSION_LOADED_MEMCACHE')) {
		error_log("The /metrics route requires a valid 'options.cache' "
			. "configuration; no cache is configured.");
		return http_response_code(417); // EXPECTATION_FAILED
	}

	global $registry;

	// First, we grab the set of metrics we're interested in in the
	// form of a cached JSON list, if we can.
	$metrics = get_cache_value("prometheus_metrics");
	if (!$metrics)
		$metrics = array();
	else
		$metrics = json_decode($metrics);

	// Now, we walk through each of those list values one by one,
	// which happen to be JSON-serialized associative arrays,
	// and process each metric via its associative array's contents:
	// The route path and the query string.
	// See web/html/index.php for the creation of such metrics.
	foreach ($metrics as $metric) {
		$data = json_decode($metric, true);

		$anchor = $data['anchor'];
		$path = $data['path'];
		$type = $data['type'];
		$key = "$path:$type";

		$labels = ["method", "route"];
		if ($type)
			array_push($labels, "type");

		$count = get_cache_value("prometheus:$key");
		$gauge = $registry->getOrRegisterGauge(
			'aurweb',
			$anchor,
			'A metric count for the aurweb platform.',
			$labels
		);

		$label_values = [$data['method'], $data['path']];
		if ($type)
			array_push($label_values, $type);

		$gauge->set($count, $label_values);
	}

	// Construct the results from RenderTextFormat renderer and
	// registry's samples.
	$renderer = new RenderTextFormat();
	$result = $renderer->render($registry->getMetricFamilySamples());

	// Output the results with the right content type header.
	http_response_code(200); // OK
	header('Content-Type: ' . RenderTextFormat::MIME_TYPE);
	echo $result;
}

?>
