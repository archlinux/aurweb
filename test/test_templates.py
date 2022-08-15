import re

from typing import Any

import pytest

import aurweb.filters  # noqa: F401

from aurweb import config, db, templates, time
from aurweb.filters import as_timezone, number_format
from aurweb.filters import timestamp_to_datetime as to_dt
from aurweb.models import Package, PackageBase, User
from aurweb.models.account_type import USER_ID
from aurweb.models.license import License
from aurweb.models.package_license import PackageLicense
from aurweb.models.package_relation import PackageRelation
from aurweb.models.relation_type import PROVIDES_ID, REPLACES_ID
from aurweb.templates import base_template, make_context, register_filter, register_function
from aurweb.testing.html import parse_root
from aurweb.testing.requests import Request

GIT_CLONE_URI_ANON = "anon_%s"
GIT_CLONE_URI_PRIV = "priv_%s"


@register_filter("func")
def func():
    pass


@register_function("function")
def function():
    pass


def create_user(username: str) -> User:
    with db.begin():
        user = db.create(User, Username=username,
                         Email=f"{username}@example.org",
                         Passwd="testPassword",
                         AccountTypeID=USER_ID)
    return user


def create_pkgrel(package: Package, reltype_id: int, relname: str) \
        -> PackageRelation:
    return db.create(PackageRelation,
                     Package=package,
                     RelTypeID=reltype_id,
                     RelName=relname)


@pytest.fixture
def user(db_test) -> User:
    user = create_user("test")
    yield user


@pytest.fixture
def pkgbase(user: User) -> PackageBase:
    now = time.utcnow()
    with db.begin():
        pkgbase = db.create(PackageBase, Name="test-pkg", Maintainer=user,
                            SubmittedTS=now, ModifiedTS=now)
    yield pkgbase


@pytest.fixture
def package(user: User, pkgbase: PackageBase) -> Package:
    with db.begin():
        pkg = db.create(Package, PackageBase=pkgbase, Name=pkgbase.Name)
    yield pkg


def create_license(pkg: Package, license_name: str) -> PackageLicense:
    lic = db.create(License, Name=license_name)
    pkglic = db.create(PackageLicense, License=lic, Package=pkg)
    return pkglic


def test_register_function_exists_key_error():
    """ Most instances of register_filter are tested through module
    imports or template renders, so we only test failures here. """
    with pytest.raises(KeyError):
        @register_function("function")
        def some_func():
            pass


def test_commit_hash():
    # Hashes we'll use for this test. long_commit_hash should be
    # shortened to commit_hash for rendering.
    commit_hash = "abcdefg"
    long_commit_hash = commit_hash + "1234567"

    def config_get_with_fallback(section: str, option: str,
                                 fallback: str = None) -> str:
        if section == "devel" and option == "commit_hash":
            return long_commit_hash
        return config.original_get_with_fallback(section, option, fallback)

    # Fake config.get_with_fallback.
    config.original_get_with_fallback = config.get_with_fallback
    config.get_with_fallback = config_get_with_fallback

    request = Request()
    context = templates.make_context(request, "Test Context")
    render = templates.render_raw_template(request, "index.html", context)

    # We've faked config.get_with_fallback to return a "valid" commit_hash
    # when queried. Test that the expected render occurs.
    commit_url = config.get("devel", "commit_url")
    expected = commit_url % commit_hash
    assert expected in render
    assert f"HEAD@{commit_hash}" in render
    assert long_commit_hash not in render

    # Restore config.get_with_fallback.
    config.get_with_fallback = config.original_get_with_fallback
    config.original_get_with_fallback = None

    # Now, we no longer fake the commit_hash option: no commit
    # is displayed in the footer. Assert this expectation.
    context = templates.make_context(request, "Test Context")
    render = templates.render_raw_template(request, "index.html", context)
    assert commit_hash not in render


def pager_context(num_packages: int) -> dict[str, Any]:
    return {
        "request": Request(),
        "singular": "%d package found.",
        "plural": "%d packages found.",
        "prefix": "/packages",
        "total": num_packages,
        "O": 0,
        "PP": 50
    }


def test_pager_no_results():
    """ Test the pager partial with no results. """
    num_packages = 0
    context = pager_context(num_packages)
    body = base_template("partials/pager.html").render(context)

    root = parse_root(body)
    stats = root.xpath('//div[@class="pkglist-stats"]/p')
    expected = "0 packages found."
    assert stats[0].text.strip() == expected


def test_pager():
    """ Test the pager partial with two pages of results. """
    num_packages = 100
    context = pager_context(num_packages)
    body = base_template("partials/pager.html").render(context)

    root = parse_root(body)
    stats = root.xpath('//div[@class="pkglist-stats"]/p')
    stats = re.sub(r"\s{2,}", " ", stats[0].text.strip())
    expected = f"{num_packages} packages found. Page 1 of 2."
    assert stats == expected


def check_package_details(content: str, pkg: Package) -> None:
    """
    Perform assertion checks against package details.
    """
    pkgbase = pkg.PackageBase

    root = parse_root(content)
    pkginfo = root.xpath('//table[@id="pkginfo"]')[0]
    rows = pkginfo.xpath("./tr")

    # Check Git Clone URL.
    git_clone_uris = rows[0].xpath("./td/a")
    anon_uri, priv_uri = git_clone_uris
    pkgbasename = pkgbase.Name
    assert anon_uri.text.strip() == GIT_CLONE_URI_ANON % pkgbasename
    assert priv_uri.text.strip() == GIT_CLONE_URI_PRIV % pkgbasename

    # Check Package Base.
    pkgbase_markup = rows[1].xpath("./td/a")[0]
    assert pkgbase_markup.text.strip() == pkgbasename

    # Check Description.
    desc = rows[2].xpath("./td")[0]
    assert desc.text.strip() == str(pkg.Description)

    # Check URL, for which we have none. In this case, no <a> should
    # be used since we have nothing to link.
    url = rows[3].xpath("./td")[0]
    assert url.text.strip() == str(pkg.URL)

    # Check Keywords, which should be empty.
    keywords = rows[4].xpath("./td/form/div/input")[0]
    assert keywords.attrib["value"] == str()

    i = 4
    licenses = pkg.package_licenses.all()
    if licenses:
        i += 1
        expected = ", ".join([p.License.Name for p in licenses])
        license_markup = rows[i].xpath("./td")[0]
        assert license_markup.text.strip() == expected
    else:
        assert "Licenses" not in content

    provides = pkg.package_relations.filter(
        PackageRelation.RelTypeID == PROVIDES_ID
    ).all()
    if provides:
        i += 1
        expected = ", ".join([p.RelName for p in provides])
        provides_markup = rows[i].xpath("./td")[0]
        assert provides_markup.text.strip() == expected
    else:
        assert "Provides" not in content

    replaces = pkg.package_relations.filter(
        PackageRelation.RelTypeID == REPLACES_ID
    ).all()
    if replaces:
        i += 1
        expected = ", ".join([r.RelName for r in replaces])
        replaces_markup = rows[i].xpath("./td")[0]
        assert replaces_markup.text.strip() == expected
    else:
        assert "Replaces" not in content

    # Check Submitter.
    selector = "./td" if not pkg.PackageBase.Submitter else "./td/a"
    i += 1
    submitter = rows[i].xpath(selector)[0]
    assert submitter.text.strip() == str(pkg.PackageBase.Submitter)

    # Check Maintainer.
    selector = "./td" if not pkg.PackageBase.Maintainer else "./td/a"
    i += 1
    maintainer = rows[i].xpath(selector)[0]
    assert maintainer.text.strip() == str(pkg.PackageBase.Maintainer)

    # Check Packager.
    selector = "./td" if not pkg.PackageBase.Packager else "./td/a"
    i += 1
    packager = rows[i].xpath(selector)[0]
    assert packager.text.strip() == str(pkg.PackageBase.Packager)

    # Check Votes.
    i += 1
    votes = rows[i].xpath("./td")[0]
    assert votes.text.strip() == str(pkg.PackageBase.NumVotes)

    # Check Popularity; for this package, a number_format of 6 places is used.
    i += 1
    pop = rows[i].xpath("./td")[0]
    assert pop.text.strip() == number_format(0, 6)

    # Check First Submitted
    date_fmt = "%Y-%m-%d %H:%M (%Z)"
    i += 1
    first_submitted = rows[i].xpath("./td")[0]
    converted_dt = as_timezone(to_dt(pkg.PackageBase.SubmittedTS), "UTC")
    expected = converted_dt.strftime(date_fmt)
    assert first_submitted.text.strip() == expected

    # Check Last Updated.
    i += 1
    last_updated = rows[i].xpath("./td")[0]
    converted_dt = as_timezone(to_dt(pkg.PackageBase.ModifiedTS), "UTC")
    expected = converted_dt.strftime(date_fmt)
    assert last_updated.text.strip() == expected


def test_package_details(user: User, package: Package):
    """ Test package details with most fields populated, but not all. """
    request = Request(user=user, authenticated=True)
    context = make_context(request, "Test Details")
    context.update({
        "request": request,
        "git_clone_uri_anon": GIT_CLONE_URI_ANON,
        "git_clone_uri_priv": GIT_CLONE_URI_PRIV,
        "pkgbase": package.PackageBase,
        "pkg": package,
        "comaintainers": [],
    })

    base = base_template("partials/packages/details.html")
    body = base.render(context, show_package_details=True)
    check_package_details(body, package)


def test_package_details_filled(user: User, package: Package):
    """ Test package details with all fields populated. """

    pkgbase = package.PackageBase
    with db.begin():
        # Setup Submitter and Packager; Maintainer is already set to `user`.
        pkgbase.Submitter = pkgbase.Packager = user

        # Create two licenses.
        create_license(package, "TPL")  # Testing Public License
        create_license(package, "TPL2")  # Testing Public License 2

        # Add provides.
        create_pkgrel(package, PROVIDES_ID, "test-provider")

        # Add replaces.
        create_pkgrel(package, REPLACES_ID, "test-replacement")

    request = Request(user=user, authenticated=True)
    context = make_context(request, "Test Details")
    context.update({
        "request": request,
        "git_clone_uri_anon": GIT_CLONE_URI_ANON,
        "git_clone_uri_priv": GIT_CLONE_URI_PRIV,
        "pkgbase": package.PackageBase,
        "pkg": package,
        "comaintainers": [],
        "licenses": package.package_licenses,
        "provides": package.package_relations.filter(
            PackageRelation.RelTypeID == PROVIDES_ID),
        "replaces": package.package_relations.filter(
            PackageRelation.RelTypeID == REPLACES_ID),
    })

    base = base_template("partials/packages/details.html")
    body = base.render(context, show_package_details=True)
    check_package_details(body, package)
