<?php

if (!defined('CACHE_TYPE')) {
	define('CACHE_TYPE', 'NONE');
}

# Check if APC extension is loaded, and set cache prefix if it is.
if (CACHE_TYPE == 'APC' && !defined('EXTENSION_LOADED_APC')) {
	define('EXTENSION_LOADED_APC', extension_loaded('apc'));
	define('CACHE_PREFIX', 'aur:');
}

# Check if memcache extension is loaded, and set cache prefix if it is.
if (CACHE_TYPE == 'MEMCACHE' && !defined('EXTENSION_LOADED_MEMCACHE')) {
	define('EXTENSION_LOADED_MEMCACHE', extension_loaded('memcached'));
	define('CACHE_PREFIX', 'aur:');
	global $memcache;
	$memcache = new Memcached();
	$mcs = defined('MEMCACHE_SERVERS') ? MEMCACHE_SERVERS : '127.0.0.1:11211';
	foreach (explode(',', $mcs) as $elem) {
		$telem = trim($elem);
		$mcserver = explode(':', $telem);
		$memcache->addServer($mcserver[0], intval($mcserver[1]));
	}
}

# Set a value in the cache (currently APC) if cache is available for use. If
# not available, this becomes effectively a no-op (return value is
# false). Accepts an optional TTL (defaults to 600 seconds).
function set_cache_value($key, $value, $ttl=600) {
	$status = false;
	if (defined('EXTENSION_LOADED_APC')) {
		$status = apc_store(CACHE_PREFIX.$key, $value, $ttl);
	}
	if (defined('EXTENSION_LOADED_MEMCACHE')) {
		global $memcache;
		$status = $memcache->set(CACHE_PREFIX.$key, $value, $ttl);
	}
	return $status;
}

# Get a value from the cache (currently APC) if cache is available for use. If
# not available, this returns false (optionally sets passed in variable $status
# to false, much like apc_fetch() behaves). This allows for testing the fetch
# result appropriately even in the event that a 'false' value was the value in
# the cache.
function get_cache_value($key, &$status=false) {
	if(defined('EXTENSION_LOADED_APC')) {
		$ret = apc_fetch(CACHE_PREFIX.$key, $status);
		if ($status) {
			return $ret;
		}
	}
	if (defined('EXTENSION_LOADED_MEMCACHE')) {
		global $memcache;
		$ret = $memcache->get(CACHE_PREFIX.$key);
		if (!$ret) {
			$status = false;
		}
		else {
			$status = true;
		}
		return $ret;
	}
	return $status;
}

# Run a simple db query, retrieving and/or caching the value if APC is
# available for use. Accepts an optional TTL value (defaults to 600 seconds).
function db_cache_value($dbq, $dbh, $key, $ttl=600) {
	$status = false;
	$value = get_cache_value($key, $status);
	if (!$status) {
		$result = $dbh->query($dbq);
		$row = $result->fetch(PDO::FETCH_NUM);
		$value = $row[0];
		set_cache_value($key, $value, $ttl);
	}
	return $value;
}

?>
