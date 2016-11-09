<?php

include_once("confparser.inc.php");

class DB {

	/**
	 * A database object
	 */
	private static $dbh = null;

	/**
	 * Return an already existing database object or newly instantiated object
	 *
	 * @return \PDO A database connection using PDO
	 */
	public static function connect() {
		if (self::$dbh === null) {
			try {
				$backend = config_get('database', 'backend');
				$host = config_get('database', 'host');
				$socket = config_get('database', 'socket');
				$name = config_get('database', 'name');
				$user = config_get('database', 'user');
				$password = config_get('database', 'password');

				if ($backend == "mysql") {
					$dsn = $backend .
						':host=' . $host .
						';unix_socket=' . $socket .
						';dbname=' . $name;

					self::$dbh = new PDO($dsn, $user, $password);
					self::$dbh->exec("SET NAMES 'utf8' COLLATE 'utf8_general_ci';");
				} else if ($backend == "sqlite") {
					$dsn = $backend .
						":" . $name;

					self::$dbh = new PDO($dsn, null, null);
				} else {
					die("Error - " . $backend . " is not supported by aurweb");
				}

			} catch (PDOException $e) {
				die('Error - Could not connect to AUR database');
			}
		}

		return self::$dbh;
	}
}
