<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../lang');

include("aur.inc");

include("feedcreator.class.php");

#If there's a cached version <1hr old, won't regenerate now
$rss = new UniversalFeedCreator();
$rss->useCached("RSS2.0", "xml/newestpkg.xml", 1800);

#All the general RSS setup
$rss->title = "AUR Newest Packages";
$rss->description = "The latest and greatest packages in the AUR";
$rss->link = "http" . ($_SERVER["HTTPS"]=='on'?"s":"") . "://".$_SERVER['HTTP_HOST'];
$rss->syndicationURL = "http" . ($_SERVER["HTTPS"]=='on'?"s":"") . "://".$_SERVER['HTTP_HOST']."/rss2.php";
$image = new FeedImage();
$image->title = "AUR";
$image->url = "http" . ($_SERVER["HTTPS"]=='on'?"s":"") . "://".$_SERVER['HTTP_HOST']."/images/AUR-logo-80.png";
$image->link = "http" . ($_SERVER["HTTPS"]=='on'?"s":"") . "://".$_SERVER['HTTP_HOST'];
$image->description = "AUR Newest Packages Feed";
$rss->image = $image;

#Get the latest packages and add items for them
$dbh = db_connect();
$q = "SELECT * FROM Packages ";
$q.= "WHERE DummyPkg != 1 ";
$q.= "ORDER BY SubmittedTS DESC ";
$q.= "LIMIT 0 , 20";
$result = db_query($q, $dbh);

$protocol = 'http';

if (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] == 'on')
	$protocol = 'https';


while ($row = mysql_fetch_assoc($result)) {
	$item = new FeedItem();
	$item->title = $row["Name"];

	$item->link = $protocol . "://".$_SERVER['HTTP_HOST'] .
	'/packages.php?ID='.$row["ID"];

	$item->description = $row["Description"];
	$item->date = intval($row["SubmittedTS"]);
	$item->source = $protocol . "://".$_SERVER['HTTP_HOST'];
	$item->author = username_from_id($row["MaintainerUID"]);
	$rss->addItem($item);
}

#save it so that useCached() can find it
$rss->saveFeed("RSS2.0","xml/newestpkg.xml",true);

# $Id$
# vim: ts=2 sw=2 noet ft=php
?>
