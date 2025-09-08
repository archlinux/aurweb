import hashlib

from fastapi import APIRouter, Request
from fastapi.responses import Response
from feedgen.feed import FeedGenerator

from aurweb import config, db, filters
from aurweb.cache import lambda_cache
from aurweb.models import Package, PackageBase

router = APIRouter()


def make_rss_feed(request: Request, packages: list):
    """Create an RSS Feed string for some packages.

    :param request: A FastAPI request
    :param packages: A list of packages to add to the RSS feed
    :return: RSS Feed string
    """

    feed = FeedGenerator()
    feed.title("AUR Newest Packages")
    feed.description("The latest and greatest packages in the AUR")
    base = f"{request.url.scheme}://{request.url.netloc}"
    feed.link(href=base, rel="alternate")
    feed.link(href=f"{base}/rss", rel="self")
    feed.image(
        title="AUR Newest Packages",
        url=f"{base}/static/css/archnavbar/aurlogo.png",
        link=base,
        description="AUR Newest Packages Feed",
    )

    for pkg in packages:
        entry = feed.add_entry(order="append")
        entry.title(pkg.Name)
        entry.link(href=f"{base}/packages/{pkg.Name}", rel="alternate")
        entry.description(pkg.Description or str())
        dt = filters.timestamp_to_datetime(pkg.Timestamp)
        dt = filters.as_timezone(dt, request.user.Timezone)
        entry.pubDate(dt.strftime("%Y-%m-%d %H:%M:%S%z"))
        entry.guid(f"{pkg.Name}-{pkg.Timestamp}")

    return feed.rss_str()


@router.get("/rss/")
async def rss(request: Request):
    packages = (
        db.query(Package)
        .join(PackageBase)
        .order_by(PackageBase.SubmittedTS.desc())
        .limit(100)
        .with_entities(
            Package.Name,
            Package.Description,
            PackageBase.SubmittedTS.label("Timestamp"),
        )
    )

    # we use redis for caching the results of the feedgen
    cache_expire = config.getint("cache", "expiry_time_rss", 300)
    feed = lambda_cache("rss", lambda: make_rss_feed(request, packages), cache_expire)

    latest_timestamp = None
    if packages.count() > 0:
        last_modified = filters.timestamp_to_datetime(packages[-1].Timestamp)
        last_modified = filters.as_timezone(last_modified, request.user.Timezone)
        latest_timestamp = last_modified.strftime("%Y-%m-%d %H:%M:%S%z")

    response = Response(feed, media_type="application/rss+xml")
    add_cache_headers(response, latest_timestamp, cache_expire)

    # Handle conditional request
    if_none_match = request.headers.get("If-None-Match")
    if (
        if_none_match
        and "ETag" in response.headers
        and if_none_match == response.headers["ETag"]
    ):
        return Response(status_code=304)

    return response


@router.get("/rss/modified")
async def rss_modified(request: Request):
    packages = (
        db.query(Package)
        .join(PackageBase)
        .order_by(PackageBase.ModifiedTS.desc())
        .limit(100)
        .with_entities(
            Package.Name,
            Package.Description,
            PackageBase.ModifiedTS.label("Timestamp"),
        )
    )

    # we use redis for caching the results of the feedgen
    cache_expire = config.getint("cache", "expiry_time_rss", 300)
    feed = lambda_cache(
        "rss_modified", lambda: make_rss_feed(request, packages), cache_expire
    )

    latest_timestamp = None
    if packages.count() > 0:
        last_modified = filters.timestamp_to_datetime(packages[-1].Timestamp)
        last_modified = filters.as_timezone(last_modified, request.user.Timezone)
        latest_timestamp = last_modified.strftime("%Y-%m-%d %H:%M:%S%z")

    response = Response(feed, media_type="application/rss+xml")
    add_cache_headers(response, latest_timestamp, cache_expire)

    # Handle conditional request
    if_none_match = request.headers.get("If-None-Match")
    if (
        if_none_match
        and "ETag" in response.headers
        and if_none_match == response.headers["ETag"]
    ):
        return Response(status_code=304)

    return response


def add_cache_headers(
    response: Response, latest_timestamp: str | None, cache_expire: int
) -> None:
    """Add HTTP caching headers to the RSS feed response.

    :param response: The FastAPI Response object
    :param cache_expire: Cache expiration time in seconds
    """
    # Set Cache-Control header
    response.headers["Cache-Control"] = f"public, max-age={cache_expire}"

    # Set Last-Modified header if not None
    if latest_timestamp is not None:
        response.headers["Last-Modified"] = latest_timestamp

    # Set ETag header (based on content hash)
    if hasattr(response, "body") and response.body:
        etag = hashlib.md5(response.body).hexdigest()
        response.headers["ETag"] = f'"{etag}"'
