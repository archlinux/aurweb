<?php
/**
 * AurJSON
 *
 * This file contains the AurRPC remote handling class
 **/
if (!extension_loaded('json')) {
    dl('json.so');
}

include_once("aur.inc");

/**
 * This class defines a remote interface for fetching data
 * from the AUR using JSON formatted elements.
 * @package rpc
 * @subpackage classes
 **/
class AurJSON {
    private $dbh = false;
    private $exposed_methods = array('search','info','msearch');
    private $fields = array('Packages.ID','Name','Version','CategoryID',
	'Description', 'LocationID', 'URL','URLPath','License','NumVotes',
	'OutOfDate');

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
        if ( in_array($http_data['type'], $this->exposed_methods) ) {
            // set up db connection.
            $this->dbh = db_connect();

            // ugh. this works. I hate you php.
            $json = call_user_func(array(&$this,$http_data['type']),
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
    private function json_error($msg){
        // set content type header to app/json
        header('content-type: application/json');
        return $this->json_results('error',$msg);
    }

    /**
     * Returns a JSON formatted result data.
     * @param $type The response method type.
     * @param $data The result data to return
     * @return mixed A json formatted result response.
     **/
    private function json_results($type,$data){
        return json_encode( array('type' => $type, 'results' => $data) );
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

        $query = "SELECT " . implode(',', $this->fields) .
            " FROM Packages WHERE DummyPkg=0 AND " .
            "  ( Name LIKE '%{$keyword_string}%' OR " .
            "    Description LIKE '%{$keyword_string}%' )";
        $result = db_query($query, $this->dbh);

        if ( $result && (mysql_num_rows($result) > 0) ) {
            $search_data = array();
            while ( $row = mysql_fetch_assoc($result) ) {
                array_push($search_data, $row);
            }

            mysql_free_result($result);
            return $this->json_results('search', $search_data);
        }
        else {
            return $this->json_error('No results found');
        }
    }

    /**
     * Returns the info on a specific package.
     * @param $pqdata The ID or name of the package. Package Query Data.
     * @return mixed Returns an array of value data containing the package data
     **/
    private function info($pqdata) {
        $base_query = "SELECT " . implode(',', $this->fields) .
            " FROM Packages WHERE DummyPkg=0 AND ";

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
            $query_stub = printf("Name=\"%s\"",
                mysql_real_escape_string($pqdata));
        }

        $result = db_query($base_query.$query_stub, $this->dbh);

        if ( $result && (mysql_num_rows($result) > 0) ) {
            $row = mysql_fetch_assoc($result);
            mysql_free_result($result);
            foreach($row as $name => $value) {
                $converted = utf8_encode($value);
                if ($converted) {
                    $row[$name] = $converted;
                }
                else {
                    $row[$name] = "[PKGBUILD error: non-UTF8 character]";
                }
            }
            return $this->json_results('info', $row);
        }
        else {
            return $this->json_error('No result found');
        }
    }

    /**
     * Returns all the packages for a specific maintainer.
     * @param $maintainer The name of the maintainer.
     * @return mixed Returns an array of value data containing the package data
     **/
    private function msearch($maintainer) {
        $maintainer = mysql_real_escape_string($maintainer, $this->dbh);
        $fields = implode(',', $this->fields);

        $query = "SELECT Users.Username as Maintainer, {$fields} " .
            " FROM Packages, Users " .
            "        WHERE Packages.MaintainerUID = Users.ID AND " .
            "              Users.Username = '{$maintainer}'";
        $result = db_query($query, $this->dbh);

        if ( $result && (mysql_num_rows($result) > 0) ) {
            $packages = array();
            while ( $row = mysql_fetch_assoc($result) ) {
                array_push($packages, $row);
            }
            mysql_free_result($result);
            return $this->json_results('msearch', $packages);
        }
        else {
            return $this->json_error('No results found');
        }
    }
}

