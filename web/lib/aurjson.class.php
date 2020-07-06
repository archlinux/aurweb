<?php

include_once("aur.inc.php");
include_once("pkgfuncs.inc.php");

/*
 * This class defines a remote interface for fetching data from the AUR using
 * JSON formatted elements.
 *
 * @package rpc
 * @subpackage classes
 */
class AurJSON {
	private $dbh = false;
	private $version = 1;
	private static $exposed_methods = array(
		'search', 'info', 'multiinfo', 'msearch', 'suggest',
		'suggest-pkgbase', 'get-comment-form'
	);
	private static $exposed_fields = array(
		'name', 'name-desc', 'maintainer',
		'depends', 'makedepends', 'checkdepends', 'optdepends'
	);
	private static $exposed_depfields = array(
		'depends', 'makedepends', 'checkdepends', 'optdepends'
	);
	private static $fields_v1 = array(
		'Packages.ID', 'Packages.Name',
		'PackageBases.ID AS PackageBaseID',
		'PackageBases.Name AS PackageBase', 'Version',
		'Description', 'URL', 'NumVotes', 'OutOfDateTS AS OutOfDate',
		'Users.UserName AS Maintainer',
		'SubmittedTS AS FirstSubmitted', 'ModifiedTS AS LastModified',
		'Licenses.Name AS License'
	);
	private static $fields_v2 = array(
		'Packages.ID', 'Packages.Name',
		'PackageBases.ID AS PackageBaseID',
		'PackageBases.Name AS PackageBase', 'Version',
		'Description', 'URL', 'NumVotes', 'OutOfDateTS AS OutOfDate',
		'Users.UserName AS Maintainer',
		'SubmittedTS AS FirstSubmitted', 'ModifiedTS AS LastModified'
	);
	private static $fields_v4 = array(
		'Packages.ID', 'Packages.Name',
		'PackageBases.ID AS PackageBaseID',
		'PackageBases.Name AS PackageBase', 'Version',
		'Description', 'URL', 'NumVotes', 'Popularity',
		'OutOfDateTS AS OutOfDate', 'Users.UserName AS Maintainer',
		'SubmittedTS AS FirstSubmitted', 'ModifiedTS AS LastModified'
	);
	private static $numeric_fields = array(
		'ID', 'PackageBaseID', 'NumVotes', 'OutOfDate',
		'FirstSubmitted', 'LastModified'
	);
	private static $decimal_fields = array(
		'Popularity'
	);

	/*
	 * Handles post data, and routes the request.
	 *
	 * @param string $post_data The post data to parse and handle.
	 *
	 * @return string The JSON formatted response data.
	 */
	public function handle($http_data) {
		/*
		 * Unset global aur.inc.php Pragma header. We want to allow
		 * caching of data in proxies, but require validation of data
		 * (if-none-match) if possible.
		 */
		header_remove('Pragma');
		/*
		 * Overwrite cache-control header set in aur.inc.php to allow
		 * caching, but require validation.
		 */
		header('Cache-Control: public, must-revalidate, max-age=0');
		header('Content-Type: application/json, charset=utf-8');

		if (isset($http_data['v'])) {
			$this->version = intval($http_data['v']);
		}
		if ($this->version < 1 || $this->version > 6) {
			return $this->json_error('Invalid version specified.');
		}

		if (!isset($http_data['type']) || !isset($http_data['arg'])) {
			return $this->json_error('No request type/data specified.');
		}
		if (!in_array($http_data['type'], self::$exposed_methods)) {
			return $this->json_error('Incorrect request type specified.');
		}

		if (isset($http_data['search_by']) && !isset($http_data['by'])) {
			$http_data['by'] = $http_data['search_by'];
		}
		if (isset($http_data['by']) && !in_array($http_data['by'], self::$exposed_fields)) {
			return $this->json_error('Incorrect by field specified.');
		}

		$this->dbh = DB::connect();

		if ($this->check_ratelimit($_SERVER['REMOTE_ADDR'])) {
			header("HTTP/1.1 429 Too Many Requests");
			return $this->json_error('Rate limit reached');
		}

		$type = str_replace('-', '_', $http_data['type']);
		if ($type == 'info' && $this->version >= 5) {
			$type = 'multiinfo';
		}
		$json = call_user_func(array(&$this, $type), $http_data);

		$etag = md5($json);
		header("Etag: \"$etag\"");
		/*
		 * Make sure to strip a few things off the
		 * if-none-match header. Stripping whitespace may not
		 * be required, but removing the quote on the incoming
		 * header is required to make the equality test.
		 */
		$if_none_match = isset($_SERVER['HTTP_IF_NONE_MATCH']) ?
			trim($_SERVER['HTTP_IF_NONE_MATCH'], "\t\n\r\" ") : false;
		if ($if_none_match && $if_none_match == $etag) {
			header('HTTP/1.1 304 Not Modified');
			return;
		}

		if (isset($http_data['callback'])) {
			$callback = $http_data['callback'];
			if (!preg_match('/^[a-zA-Z0-9()_.]{1,128}$/D', $callback)) {
				return $this->json_error('Invalid callback name.');
			}
			header('content-type: text/javascript');
			return '/**/' . $callback . '(' . $json . ')';
		} else {
			header('content-type: application/json');
			return $json;
		}
	}

	/*
	 * Check if an IP needs to be rate limited.
	 *
	 * @param $ip IP of the current request
	 *
	 * @return true if IP needs to be rate limited, false otherwise.
	 */
	private function check_ratelimit($ip) {
		$limit = config_get("ratelimit", "request_limit");
		if ($limit == 0) {
			return false;
		}

		$this->update_ratelimit($ip);

		$status = false;
		$value = get_cache_value('ratelimit:' . $ip, $status);
		if (!$status) {
			$stmt = $this->dbh->prepare("
				SELECT Requests FROM ApiRateLimit
				WHERE IP = :ip");
			$stmt->bindParam(":ip", $ip);
			$result = $stmt->execute();

			if (!$result) {
				return false;
			}

			$row = $stmt->fetch(PDO::FETCH_ASSOC);
			$value = $row['Requests'];
		}

		return $value > $limit;
	}

	/*
	 * Update a rate limit for an IP by increasing it's requests value by one.
	 *
	 * @param $ip IP of the current request
	 *
	 * @return void
	 */
	private function update_ratelimit($ip) {
		$window_length = config_get("ratelimit", "window_length");
		$db_backend = config_get("database", "backend");
		$time = time();
		$deletion_time = $time - $window_length;

		/* Try to use the cache. */
		$status = false;
		$value = get_cache_value('ratelimit-ws:' . $ip, $status);
		if (!$status || ($status && $value < $deletion_time)) {
			if (set_cache_value('ratelimit-ws:' . $ip, $time, $window_length) &&
				set_cache_value('ratelimit:' . $ip, 1, $window_length)) {
				return;
			}
		} else {
			$value = get_cache_value('ratelimit:' . $ip, $status);
			if ($status && set_cache_value('ratelimit:' . $ip, $value + 1, $window_length))
				return;
		}

		/* Clean up old windows. */
		$stmt = $this->dbh->prepare("
			DELETE FROM ApiRateLimit
			WHERE WindowStart < :time");
		$stmt->bindParam(":time", $deletion_time);
		$stmt->execute();

		if ($db_backend == "mysql") {
			$stmt = $this->dbh->prepare("
				INSERT INTO ApiRateLimit
				(IP, Requests, WindowStart)
				VALUES (:ip, 1, :window_start)
				ON DUPLICATE KEY UPDATE Requests=Requests+1");
			$stmt->bindParam(":ip", $ip);
			$stmt->bindParam(":window_start", $time);
			$stmt->execute();
		} elseif ($db_backend == "sqlite") {
			$stmt = $this->dbh->prepare("
				INSERT OR IGNORE INTO ApiRateLimit
				(IP, Requests, WindowStart)
				VALUES (:ip, 0, :window_start);");
			$stmt->bindParam(":ip", $ip);
			$stmt->bindParam(":window_start", $time);
			$stmt->execute();

			$stmt = $this->dbh->prepare("
				UPDATE ApiRateLimit
				SET Requests = Requests + 1
				WHERE IP = :ip");
			$stmt->bindParam(":ip", $ip);
			$stmt->execute();
		} else {
			throw new RuntimeException("Unknown database backend");
		}
	}

	/*
	 * Returns a JSON formatted error string.
	 *
	 * @param $msg The error string to return
	 *
	 * @return mixed A json formatted error response.
	 */
	private function json_error($msg) {
		header('content-type: application/json');
		if ($this->version < 3) {
			return $this->json_results('error', 0, $msg, NULL);
		} elseif ($this->version >= 3) {
			return $this->json_results('error', 0, array(), $msg);
		}
	}

	/*
	 * Returns a JSON formatted result data.
	 *
	 * @param $type The response method type.
	 * @param $count The number of results to return
	 * @param $data The result data to return
	 * @param $error An error message to include in the response
	 *
	 * @return mixed A json formatted result response.
	 */
	private function json_results($type, $count, $data, $error) {
		$json_array = array(
			'version' => $this->version,
			'type' => $type,
			'resultcount' => $count,
			'results' => $data
		);

		if ($error) {
			$json_array['error'] = $error;
		}

		return json_encode($json_array);
	}

	/*
	 * Get extended package details (for info and multiinfo queries).
	 *
	 * @param $pkgid The ID of the package to retrieve details for.
	 * @param $base_id The ID of the package base to retrieve details for.
	 *
	 * @return array An array containing package details.
	 */
	private function get_extended_fields($pkgid, $base_id) {
		$query = "SELECT DependencyTypes.Name AS Type, " .
			"PackageDepends.DepName AS Name, " .
			"PackageDepends.DepCondition AS Cond " .
			"FROM PackageDepends " .
			"LEFT JOIN DependencyTypes " .
			"ON DependencyTypes.ID = PackageDepends.DepTypeID " .
			"WHERE PackageDepends.PackageID = " . $pkgid . " " .
			"UNION SELECT RelationTypes.Name AS Type, " .
			"PackageRelations.RelName AS Name, " .
			"PackageRelations.RelCondition AS Cond " .
			"FROM PackageRelations " .
			"LEFT JOIN RelationTypes " .
			"ON RelationTypes.ID = PackageRelations.RelTypeID " .
			"WHERE PackageRelations.PackageID = " . $pkgid . " " .
			"UNION SELECT 'groups' AS Type, `Groups`.`Name`, '' AS Cond " .
			"FROM `Groups` INNER JOIN PackageGroups " .
			"ON PackageGroups.PackageID = " . $pkgid . " " .
			"AND PackageGroups.GroupID = `Groups`.ID " .
			"UNION SELECT 'license' AS Type, Licenses.Name, '' AS Cond " .
			"FROM Licenses INNER JOIN PackageLicenses " .
			"ON PackageLicenses.PackageID = " . $pkgid . " " .
			"AND PackageLicenses.LicenseID = Licenses.ID";
		$ttl = config_get_int('options', 'cache_pkginfo_ttl');
		$rows = db_cache_result($query, 'extended-fields:' . $pkgid, PDO::FETCH_ASSOC, $ttl);

		$type_map = array(
			'depends' => 'Depends',
			'makedepends' => 'MakeDepends',
			'checkdepends' => 'CheckDepends',
			'optdepends' => 'OptDepends',
			'conflicts' => 'Conflicts',
			'provides' => 'Provides',
			'replaces' => 'Replaces',
			'groups' => 'Groups',
			'license' => 'License',
		);
		$data = array();
		foreach ($rows as $row) {
			$type = $type_map[$row['Type']];
			$data[$type][] = $row['Name'] . $row['Cond'];
		}

		if ($this->version >= 5) {
			$query = "SELECT Keyword FROM PackageKeywords " .
				"WHERE PackageBaseID = " . intval($base_id) . " " .
				"ORDER BY Keyword ASC";
			$ttl = config_get_int('options', 'cache_pkginfo_ttl');
			$rows = db_cache_result($query, 'keywords:' . intval($base_id), PDO::FETCH_NUM, $ttl);
			$data['Keywords'] = array_map(function ($x) { return $x[0]; }, $rows);
		}

		return $data;
	}

	/*
	 * Retrieve package information (used in info, multiinfo, search and
	 * depends requests).
	 *
	 * @param $type The request type.
	 * @param $where_condition An SQL WHERE-condition to filter packages.
	 *
	 * @return mixed Returns an array of package matches.
	 */
	private function process_query($type, $where_condition) {
		$max_results = config_get_int('options', 'max_rpc_results');

		if ($this->version == 1) {
			$fields = implode(',', self::$fields_v1);
			$query = "SELECT {$fields} " .
				"FROM Packages LEFT JOIN PackageBases " .
				"ON PackageBases.ID = Packages.PackageBaseID " .
				"LEFT JOIN Users " .
				"ON PackageBases.MaintainerUID = Users.ID " .
				"LEFT JOIN PackageLicenses " .
				"ON PackageLicenses.PackageID = Packages.ID " .
				"LEFT JOIN Licenses " .
				"ON Licenses.ID = PackageLicenses.LicenseID " .
				"WHERE ${where_condition} " .
				"AND PackageBases.PackagerUID IS NOT NULL " .
				"LIMIT $max_results";
		} elseif ($this->version >= 2) {
			if ($this->version == 2 || $this->version == 3) {
				$fields = implode(',', self::$fields_v2);
			} else if ($this->version >= 4 && $this->version <= 6) {
				$fields = implode(',', self::$fields_v4);
			}
			$query = "SELECT {$fields} " .
				"FROM Packages LEFT JOIN PackageBases " .
				"ON PackageBases.ID = Packages.PackageBaseID " .
				"LEFT JOIN Users " .
				"ON PackageBases.MaintainerUID = Users.ID " .
				"WHERE ${where_condition} " .
				"AND PackageBases.PackagerUID IS NOT NULL " .
				"LIMIT $max_results";
		}
		$result = $this->dbh->query($query);

		if ($result) {
			$resultcount = 0;
			$search_data = array();
			while ($row = $result->fetch(PDO::FETCH_ASSOC)) {
				$resultcount++;
				$row['URLPath'] = sprintf(config_get('options', 'snapshot_uri'), urlencode($row['PackageBase']));
				if ($this->version < 4) {
					$row['CategoryID'] = 1;
				}

				/*
				 * Unfortunately, mysql_fetch_assoc() returns
				 * all fields as strings. We need to coerce
				 * numeric values into integers to provide
				 * proper data types in the JSON response.
				 */
				foreach (self::$numeric_fields as $field) {
					if (isset($row[$field])) {
						$row[$field] = intval($row[$field]);
					}
				}

				foreach (self::$decimal_fields as $field) {
					if (isset($row[$field])) {
						$row[$field] = floatval($row[$field]);
					}
				}

				if ($this->version >= 2 && ($type == 'info' || $type == 'multiinfo')) {
					$extfields = $this->get_extended_fields($row['ID'], $row['PackageBaseID']);
					if ($extfields) {
						$row = array_merge($row, $extfields);
					}
				}

				if ($this->version < 3) {
					if ($type == 'info') {
						$search_data = $row;
						break;
					} else {
						array_push($search_data, $row);
					}
				} elseif ($this->version >= 3) {
					array_push($search_data, $row);
				}
			}

			if ($resultcount === $max_results) {
				return $this->json_error('Too many package results.');
			}

			return $this->json_results($type, $resultcount, $search_data, NULL);
		} else {
			return $this->json_results($type, 0, array(), NULL);
		}
	}

	/*
	 * Parse the args to the multiinfo function. We may have a string or an
	 * array, so do the appropriate thing. Within the elements, both * package
	 * IDs and package names are valid; sort them into the relevant arrays and
	 * escape/quote the names.
	 *
	 * @param array $args Query parameters.
	 *
	 * @return mixed An array containing 'ids' and 'names'.
	 */
	private function parse_multiinfo_args($args) {
		if (!is_array($args)) {
			$args = array($args);
		}

		$id_args = array();
		$name_args = array();
		foreach ($args as $arg) {
			if (!$arg) {
				continue;
			}
			if ($this->version < 5 && is_numeric($arg)) {
				$id_args[] = intval($arg);
			} else {
				$name_args[] = $this->dbh->quote($arg);
			}
		}

		return array('ids' => $id_args, 'names' => $name_args);
	}

	/*
	 * Performs a fulltext mysql search of the package database.
	 *
	 * @param array $http_data Query parameters.
	 *
	 * @return mixed Returns an array of package matches.
	 */
	private function search($http_data) {
		$keyword_string = $http_data['arg'];

		if (isset($http_data['by'])) {
			$search_by = $http_data['by'];
		} else {
			$search_by = 'name-desc';
		}

		if ($search_by === 'name' || $search_by === 'name-desc') {
			if (strlen($keyword_string) < 2) {
				return $this->json_error('Query arg too small.');
			}

			if ($this->version >= 6 && $search_by === 'name-desc') {
				$where_condition = construct_keyword_search($this->dbh,
					$keyword_string, true, false);
			} else {
				$keyword_string = $this->dbh->quote(
					"%" . addcslashes($keyword_string, '%_') . "%");

				if ($search_by === 'name') {
					$where_condition = "(Packages.Name LIKE $keyword_string)";
				} else if ($search_by === 'name-desc') {
					$where_condition = "(Packages.Name LIKE $keyword_string ";
					$where_condition .= "OR Description LIKE $keyword_string)";
				}

			}
		} else if ($search_by === 'maintainer') {
			if (empty($keyword_string)) {
				$where_condition = "Users.ID is NULL";
			} else {
				$keyword_string = $this->dbh->quote($keyword_string);
				$where_condition = "Users.Username = $keyword_string ";
			}
		} else if (in_array($search_by, self::$exposed_depfields)) {
			if (empty($keyword_string)) {
				return $this->json_error('Query arg is empty.');
			} else {
				$keyword_string = $this->dbh->quote($keyword_string);
				$search_by = $this->dbh->quote($search_by);
				$subquery = "SELECT PackageDepends.DepName FROM PackageDepends ";
				$subquery .= "LEFT JOIN DependencyTypes ";
				$subquery .= "ON PackageDepends.DepTypeID = DependencyTypes.ID ";
				$subquery .= "WHERE PackageDepends.PackageID = Packages.ID ";
				$subquery .= "AND DependencyTypes.Name = $search_by";
				$where_condition = "$keyword_string IN ($subquery)";
			}
		}

		return $this->process_query('search', $where_condition);
	}

	/*
	 * Returns the info on a specific package.
	 *
	 * @param array $http_data Query parameters.
	 *
	 * @return mixed Returns an array of value data containing the package data
	 */
	private function info($http_data) {
		$pqdata = $http_data['arg'];
		if ($this->version < 5 && is_numeric($pqdata)) {
			$where_condition = "Packages.ID = $pqdata";
		} else {
			$where_condition = "Packages.Name = " . $this->dbh->quote($pqdata);
		}

		return $this->process_query('info', $where_condition);
	}

	/*
	 * Returns the info on multiple packages.
	 *
	 * @param array $http_data Query parameters.
	 *
	 * @return mixed Returns an array of results containing the package data
	 */
	private function multiinfo($http_data) {
		$pqdata = $http_data['arg'];
		$args = $this->parse_multiinfo_args($pqdata);
		$ids = $args['ids'];
		$names = $args['names'];

		if (!$ids && !$names) {
			return $this->json_error('Invalid query arguments.');
		}

		$where_condition = "";
		if ($ids) {
			$ids_value = implode(',', $args['ids']);
			$where_condition .= "Packages.ID IN ($ids_value) ";
		}
		if ($ids && $names) {
			$where_condition .= "OR ";
		}
		if ($names) {
			/*
			 * Individual names were quoted in
			 * parse_multiinfo_args().
			 */
			$names_value = implode(',', $args['names']);
			$where_condition .= "Packages.Name IN ($names_value) ";
		}

		return $this->process_query('multiinfo', $where_condition);
	}

	/*
	 * Returns all the packages for a specific maintainer.
	 *
	 * @param array $http_data Query parameters.
	 *
	 * @return mixed Returns an array of value data containing the package data
	 */
	private function msearch($http_data) {
		$http_data['by'] = 'maintainer';
		return $this->search($http_data);
	}

	/*
	 * Get all package names that start with $search.
	 *
	 * @param array $http_data Query parameters.
	 *
	 * @return string The JSON formatted response data.
	 */
	private function suggest($http_data) {
		$search = $http_data['arg'];
		$query = "SELECT Packages.Name FROM Packages ";
		$query.= "LEFT JOIN PackageBases ";
		$query.= "ON PackageBases.ID = Packages.PackageBaseID ";
		$query.= "WHERE Packages.Name LIKE ";
		$query.= $this->dbh->quote(addcslashes($search, '%_') . '%');
		$query.= " AND PackageBases.PackagerUID IS NOT NULL ";
		$query.= "ORDER BY Name ASC LIMIT 20";

		$result = $this->dbh->query($query);
		$result_array = array();

		if ($result) {
			$result_array = $result->fetchAll(PDO::FETCH_COLUMN, 0);
		}

		return json_encode($result_array);
	}

	/*
	 * Get all package base names that start with $search.
	 *
	 * @param array $http_data Query parameters.
	 *
	 * @return string The JSON formatted response data.
	 */
	private function suggest_pkgbase($http_data) {
		$search = $http_data['arg'];
		$query = "SELECT Name FROM PackageBases WHERE Name LIKE ";
		$query.= $this->dbh->quote(addcslashes($search, '%_') . '%');
		$query.= " AND PackageBases.PackagerUID IS NOT NULL ";
		$query.= "ORDER BY Name ASC LIMIT 20";

		$result = $this->dbh->query($query);
		$result_array = array();

		if ($result) {
			$result_array = $result->fetchAll(PDO::FETCH_COLUMN, 0);
		}

		return json_encode($result_array);
	}

	/**
	 * Get the HTML markup of the comment form.
	 *
	 * @param array $http_data Query parameters.
	 *
	 * @return string The JSON formatted response data.
	 */
	private function get_comment_form($http_data) {
		if (!isset($http_data['base_id']) || !isset($http_data['pkgbase_name'])) {
			$output = array(
				'success' => 0,
				'error' => __('Package base ID or package base name missing.')
			);
			return json_encode($output);
		}

		$comment_id = intval($http_data['arg']);
		$base_id = intval($http_data['base_id']);
		$pkgbase_name = $http_data['pkgbase_name'];

		list($user_id, $comment) = comment_by_id($comment_id);

		if (!has_credential(CRED_COMMENT_EDIT, array($user_id))) {
			$output = array(
				'success' => 0,
				'error' => __('You are not allowed to edit this comment.')
			);
			return json_encode($output);
		} elseif (is_null($comment)) {
			$output = array(
				'success' => 0,
				'error' => __('Comment does not exist.')
			);
			return json_encode($output);
		}

		ob_start();
		include('pkg_comment_form.php');
		$html = ob_get_clean();
		$output = array(
			'success' => 1,
			'form' => $html
		);

		return json_encode($output);
	}
}

