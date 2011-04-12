<?php
/**
 * AurJSON
 *
 * This file contains the AurRPC remote handling class
 **/
include_once("aur.inc");

/**
 * This class defines a remote interface for fetching data
 * from the AUR using JSON formatted elements.
 * @package rpc
 * @subpackage classes
 **/
class AurJSON {
    private $dbh = false;
    private static $exposed_methods = array('search', 'info', 'msearch');
    private static $fields = array(
        'Packages.ID', 'Name', 'Version', 'CategoryID',
        'Description', 'URL', 'License',
        'NumVotes', '(OutOfDateTS IS NOT NULL) AS OutOfDate'
    );

    /**
     * Handles post data, and routes the request.
     * @param string $post_data The post data to parse and handle.
     * @return string The JSON formatted response data.
     **/
    public function handle($http_data) {
        // handle error states
        if ( !isset($http_data['type']) || !isset($http_data['arg']) ) {
            return $this->json_error('No request type/data specified.');
        }

        // do the routing
        if ( in_array($http_data['type'], self::$exposed_methods) ) {
            // set up db connection.
            $this->dbh = db_connect();

            // ugh. this works. I hate you php.
            $json = call_user_func(array(&$this, $http_data['type']),
                $http_data['arg']);

            // allow rpc callback for XDomainAjax
            if ( isset($http_data['callback']) ) {
                // it is more correct to send text/javascript
                // content-type for jsonp-callback
                header('content-type: text/javascript');
                return $http_data['callback'] . "({$json})";
            }
            else {
                // set content type header to app/json
                header('content-type: application/json');
                return $json;
            }
        }
        else {
            return $this->json_error('Incorrect request type specified.');
        }
    }

    /**
     * Returns a JSON formatted error string.
     *
     * @param $msg The error string to return
     * @return mixed A json formatted error response.
     **/
    private function json_error($msg) {
        // set content type header to app/json
        header('content-type: application/json');
        return $this->json_results('error', $msg);
    }

    /**
     * Returns a JSON formatted result data.
     * @param $type The response method type.
     * @param $data The result data to return
     * @return mixed A json formatted result response.
     **/
    private function json_results($type, $data) {
        return json_encode( array('type' => $type, 'results' => $data) );
    }

    private function process_query($type, $query) {
        $result = db_query($query, $this->dbh);

        if ( $result && (mysql_num_rows($result) > 0) ) {
            $search_data = array();
            while ( $row = mysql_fetch_assoc($result) ) {
                $name = $row['Name'];
                $row['URLPath'] = URL_DIR . $name . "/" . $name . ".tar.gz";

                if ($type == 'info') {
                    $search_data = $row;
                    break;
                }
                else {
                    array_push($search_data, $row);
                }
            }

            mysql_free_result($result);
            return $this->json_results($type, $search_data);
        }
        else {
            return $this->json_error('No results found');
        }
    }

    /**
     * Performs a fulltext mysql search of the package database.
     * @param $keyword_string A string of keywords to search with.
     * @return mixed Returns an array of package matches.
     **/
    private function search($keyword_string) {
        if (strlen($keyword_string) < 2) {
            return $this->json_error('Query arg too small');
        }

        $keyword_string = mysql_real_escape_string($keyword_string, $this->dbh);
        $keyword_string = addcslashes($keyword_string, '%_');

        $query = "SELECT " . implode(',', self::$fields) .
            " FROM Packages WHERE " .
            "  ( Name LIKE '%{$keyword_string}%' OR " .
            "    Description LIKE '%{$keyword_string}%' )";

        return $this->process_query('search', $query);
    }

    /**
     * Returns the info on a specific package.
     * @param $pqdata The ID or name of the package. Package Query Data.
     * @return mixed Returns an array of value data containing the package data
     **/
    private function info($pqdata) {
        $base_query = "SELECT " . implode(',', self::$fields) .
            " FROM Packages WHERE ";

        if ( is_numeric($pqdata) ) {
            // just using sprintf to coerce the pqd to an int
            // should handle sql injection issues, since sprintf will
            // bork if not an int, or convert the string to a number 0
            $query_stub = "ID={$pqdata}";
        }
        else {
            if(get_magic_quotes_gpc()) {
                $pqdata = stripslashes($pqdata);
            }
            $query_stub = sprintf("Name=\"%s\"",
                mysql_real_escape_string($pqdata));
        }
        $query = $base_query . $query_stub;

        return $this->process_query('info', $query);
    }

    /**
     * Returns all the packages for a specific maintainer.
     * @param $maintainer The name of the maintainer.
     * @return mixed Returns an array of value data containing the package data
     **/
    private function msearch($maintainer) {
        $maintainer = mysql_real_escape_string($maintainer, $this->dbh);
        $fields = implode(',', self::$fields);

        $query = "SELECT Users.Username as Maintainer, {$fields} " .
            " FROM Packages, Users " .
            "        WHERE Packages.MaintainerUID = Users.ID AND " .
            "              Users.Username = '{$maintainer}'";

        return $this->process_query('msearch', $query);
    }
}

