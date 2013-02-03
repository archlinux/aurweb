<?php

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
				self::$dbh = new PDO(AUR_db_DSN_prefix . ":" . AUR_db_host
					. ";dbname=" . AUR_db_name, AUR_db_user, AUR_db_pass);
				self::$dbh->exec("SET NAMES 'utf8' COLLATE 'utf8_general_ci';");
			} catch (PDOException $e) {
				die('Error - Could not connect to AUR database');
			}
		}

		return self::$dbh;
	}
}
