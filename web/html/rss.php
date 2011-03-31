<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../lang');
include_once("aur.inc");
include_once("feedcreator.class.php");

#detect prefix
$protocol = $_SERVER["HTTPS"]=='on' ? "https" : "http";
$host = $_SERVER['HTTP_HOST'];

$rss = new RSSCreator20();

# Use UTF-8 (fixes FS#10706).
$rss->encoding = "UTF-8";

#If there's a cached version <1hr old, won't regenerate now
$rss->useCached("/tmp/aur-newestpkg.xml", 1800);

#All the general RSS setup
$rss->title = "AUR Newest Packages";
$rss->description = "The latest and greatest packages in the AUR";
$rss->link = "${protocol}://{$host}";
$rss->syndicationURL = "{$protocol}://{$host}/rss.php";
$image = new FeedImage();
$image->title = "AUR";
$image->url = "{$protocol}://{$host}/images/AUR-logo-80.png";
$image->link = $rss->link;
$image->description = "AUR Newest Packages Feed";
$rss->image = $image;

#Get the latest packages and add items for them
$dbh = db_connect();
$q = "SELECT * FROM Packages ";
$q.= "ORDER BY SubmittedTS DESC ";
$q.= "LIMIT 0 , 20";
$result = db_query($q, $dbh);

while ($row = mysql_fetch_assoc($result)) {
	$item = new FeedItem();
	$item->title = $row["Name"];
	$item->link = "{$protocol}://{$host}/packages.php?ID={$row["ID"]}";
	$item->description = $row["Description"];
	$item->date = intval($row["SubmittedTS"]);
	$item->source = "{$protocol}://{$host}";
	$item->author = username_from_id($row["MaintainerUID"]);
	$rss->addItem($item);
}

#save it so that useCached() can find it
$rss->saveFeed("/tmp/aur-newestpkg.xml",true);

