from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import Response
from feedgen.feed import FeedGenerator

from aurweb import db, filters
from aurweb.models import Package, PackageBase

router = APIRouter()


def make_rss_feed(request: Request, packages: list,
                  date_attr: str):
    """ Create an RSS Feed string for some packages.

    :param request: A FastAPI request
    :param packages: A list of packages to add to the RSS feed
    :param date_attr: The date attribute (DB column) to use
    :return: RSS Feed string
    """

    feed = FeedGenerator()
    feed.title("AUR Newest Packages")
    feed.description("The latest and greatest packages in the AUR")
    base = f"{request.url.scheme}://{request.url.netloc}"
    feed.link(href=base, rel="alternate")
    feed.link(href=f"{base}/rss", rel="self")
    feed.image(title="AUR Newest Packages",
               url=f"{base}/css/archnavbar/aurlogo.png",
               link=base,
               description="AUR Newest Packages Feed")

    for pkg in packages:
        entry = feed.add_entry(order="append")
        entry.title(pkg.Name)
        entry.link(href=f"{base}/packages/{pkg.Name}", rel="alternate")
        entry.link(href=f"{base}/rss", rel="self", type="application/rss+xml")
        entry.description(pkg.Description or str())

        attr = getattr(pkg.PackageBase, date_attr)
        dt = filters.timestamp_to_datetime(attr)
        dt = filters.as_timezone(dt, request.user.Timezone)
        entry.pubDate(dt.strftime("%Y-%m-%d %H:%M:%S%z"))

        entry.source(f"{base}")
        if pkg.PackageBase.Maintainer:
            entry.author(author={"name": pkg.PackageBase.Maintainer.Username})
        entry.guid(f"{pkg.Name} - {attr}")

    return feed.rss_str()


@router.get("/rss/")
async def rss(request: Request):
    packages = db.query(Package).join(PackageBase).order_by(
        PackageBase.SubmittedTS.desc()).limit(100)
    feed = make_rss_feed(request, packages, "SubmittedTS")

    response = Response(feed, media_type="application/rss+xml")
    package = packages.first()
    if package:
        dt = datetime.utcfromtimestamp(package.PackageBase.SubmittedTS)
        modified = dt.strftime("%a, %d %m %Y %H:%M:%S GMT")
        response.headers["Last-Modified"] = modified

    return response


@router.get("/rss/modified")
async def rss_modified(request: Request):
    packages = db.query(Package).join(PackageBase).order_by(
        PackageBase.ModifiedTS.desc()).limit(100)
    feed = make_rss_feed(request, packages, "ModifiedTS")

    response = Response(feed, media_type="application/rss+xml")
    package = packages.first()
    if package:
        dt = datetime.utcfromtimestamp(package.PackageBase.ModifiedTS)
        modified = dt.strftime("%a, %d %m %Y %H:%M:%S GMT")
        response.headers["Last-Modified"] = modified

    return response
