<?php
/**
 * AurJSON
 * 
 * This file contains the AurRPC remote handling class
 * @author eliott <eliott@cactuswax.net>
 * @version $Id$
 * @copyright cactuswax.net, 12 October, 2007
 * @package rpc
 **/

/**
 * This class defines a remote interface for fetching data 
 * from the AUR using JSON formatted elements.
 * @package rpc
 * @subpackage classes
 **/
class AurJSON {
    private $dbh = false;
    private $exposed_methods = array('search','info');

    /**
     * Handles post data, and routes the request.
     * @param string $post_data The post data to parse and handle.
     * @return string The JSON formatted response data.
     **/
    public function handle($http_data) {
        // set content type header to json
        header('content-type: application/json');
        // set up db connection.
        $this->dbh = db_connect();

        // handle error states
        if ( !isset($http_data['type']) || !isset($http_data['arg']) ) {
            return $this->json_error('No request type/data specified.');
        }

        // do the routing
        if ( in_array($http_data['type'], $this->exposed_methods) ) {
            // ugh. this works. I hate you php.
            $json = call_user_func_array(array(&$this,$http_data['type']),$http_data['arg']);
            // allow rpc callback for XDomainAjax
            if ( isset($http_data['callback']) ) {
                return $http_data['callback'] . "({$json})";
            }
            else {
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
        $query = sprintf(
            "SELECT Name,ID FROM Packages WHERE MATCH(Name,Description) AGAINST('%s' IN BOOLEAN MODE)", 
            mysql_real_escape_string($keyword_string, $this->dbh) );

        $result = db_query($query, $this->dbh);

        if ( $result && (mysql_num_rows($result) > 0) ) {
            $search_data = array();
            while ( $row = mysql_fetch_assoc($result) ) {
                $elem = array(
                    'Name' => $row['Name'],
                    'ID' => $row['ID'] );
                array_push($search_data,$elem);
            }
            mysql_free_result($result);
            return $this->json_results('search',$search_data);
        }
        else {
            return $this->json_error('No results found');
        }
    }

    /**
     * Returns the info on a specific package id.
     * @param $package_id The ID of the package to fetch info.
     * @return mixed Returns an array of value data containing the package data
     **/
    private function info($package_id) {
        // using sprintf to coerce the package_id to an int
        // should handle sql injection issues, since sprintf will
        // bork if not an int, or convert the string to a number
        $query = sprintf("SELECT ID,Name,Version,Description,URL,URLPath,License,NumVotes,OutOfDate FROM Packages WHERE ID=%d",$package_id);
         $result = db_query($query, $this->dbh);

        if ( $result && (mysql_num_rows($result) > 0) ) {
            $row = mysql_fetch_assoc($result);
            mysql_free_result($result);
            return $this->json_results('info',$row);
        }
        else {
            return $this->json_error('No result found');
        }
    }
}
?>
