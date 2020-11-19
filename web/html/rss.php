<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib' . PATH_SEPARATOR . '../lang');
include_once("aur.inc.php");
include_once("pkgfuncs.inc.php");
include_once("feedcreator.class.php");

#detect prefix
$protocol = isset($_SERVER["HTTPS"]) && $_SERVER["HTTPS"]=='on' ? "https" : "http";
$host = $_SERVER['HTTP_HOST'];

$feed_key = 'pkg-feed-' . $protocol;

header("Content-Type: application/rss+xml");

$bool = false;
$ret = get_cache_value($feed_key, $bool);
if ($bool) {
	echo $ret;
	exit();
}

$rss = new RSSCreator20();
$rss->cssStyleSheet = false;
$rss->xslStyleSheet = false;

# Use UTF-8 (fixes FS#10706).
$rss->encoding = "UTF-8";

#All the general RSS setup
$rss->title = "AUR Newest Packages";
$rss->description = "The latest and greatest packages in the AUR";
$rss->link = "${protocol}://{$host}";
$rss->syndicationURL = "{$protocol}://{$host}" . get_uri('/rss/');
$image = new FeedImage();
$image->title = "AUR Newest Packages";
$image->url = "{$protocol}://{$host}/css/archnavbar/aurlogo.png";
$image->link = $rss->link;
$image->description = "AUR Newest Packages Feed";
$rss->image = $image;

#Get the latest packages and add items for them
$packages = latest_pkgs(100);

foreach ($packages as $indx => $row) {
	$item = new FeedItem();
	$item->title = $row["Name"];
	$item->link = "{$protocol}://{$host}" . get_pkg_uri($row["Name"]);
	$item->description = $row["Description"];
	$item->date = intval($row["SubmittedTS"]);
	$item->source = "{$protocol}://{$host}";
	$item->author = username_from_id($row["MaintainerUID"]);
	$item->guid = $item->link;
	$rss->addItem($item);
}

#save it so that useCached() can find it
$feedContent = $rss->createFeed();
set_cache_value($feed_key, $feedContent, 600);
echo $feedContent;
?>
