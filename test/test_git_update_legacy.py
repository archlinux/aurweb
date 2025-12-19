import json

from srcinfo import parse

from aurweb.git.update_legacy import extract_arch_fields

SRCINFO = """
pkgbase = ponies
pkgdesc = Test parse
pkgver = 1.0.0
pkgrel = 1
url = https://example.com
arch = x86_64
arch = aarch64
arch = armv7h
license = GPL
depends = curl
depends = openssl
optdepends = unicorns: Extends ponies forehead with a horn
provides = horse
conflicts = horse
options = !strip
options = staticlibs
source = ponies.service
source = ponies.sysusers
source = ponies.tmpfiles
sha256sums = 9d8f9d73e5fa2b2877dde010c0d8ca6fbf47f03eb1f01b02f846026a949a0dcf
sha256sums = d005fcd009ec5404e1ec88246c31e664167f5551d6cabc35f68eb41750bfe590
sha256sums = 64022e15565a609f449090f02d53ee90ef95cffec52ae14f99e4e2132b6cffe1
source_x86_64 = filea
source_x86_64 = fileb
sha256sums_x86_64 = f486f8528292c067620e9d495f66b0af2ad55dd4dc2e9d35b11aa7dd656d487b
sha256sums_x86_64 = f486f8528292c067620e9d495f66b0af2ad55dd4dc2e9d35b11aa7dd656d487c
source_aarch64 = filex
sha256sums_aarch64 = 1f72deec0a9af5059e1350d7b5a5a93bc4d2fbef6eeaa363fda764eb9c472b7b
source_armv7h = filey
sha256sums_armv7h = 8229b4bbf43563d8b688d19a514fb0fa0a1ef0eadbd96233882a4b496fa4c8c8
pkgname = ponies
"""

EXPECTED = """
{
    "packages": {
        "ponies": {}
    },
    "pkgbase": "ponies",
    "pkgdesc": "Test parse",
    "pkgver": "1.0.0",
    "pkgrel": "1",
    "url": "https://example.com",
    "arch": [
        "x86_64",
        "aarch64",
        "armv7h"
    ],
    "license": [
        "GPL"
    ],
    "depends": [
        "curl",
        "openssl"
    ],
    "optdepends": [
        "unicorns: Extends ponies forehead with a horn"
    ],
    "provides": [
        "horse"
    ],
    "conflicts": [
        "horse"
    ],
    "options": [
        "!strip",
        "staticlibs"
    ],
    "source": [
        "ponies.service",
        "ponies.sysusers",
        "ponies.tmpfiles"
    ],
    "sha256sums": [
        "9d8f9d73e5fa2b2877dde010c0d8ca6fbf47f03eb1f01b02f846026a949a0dcf",
        "d005fcd009ec5404e1ec88246c31e664167f5551d6cabc35f68eb41750bfe590",
        "64022e15565a609f449090f02d53ee90ef95cffec52ae14f99e4e2132b6cffe1"
    ],
    "source_x86_64": [
        "filea",
        "fileb"
    ],
    "sha256sums_x86_64": [
        "f486f8528292c067620e9d495f66b0af2ad55dd4dc2e9d35b11aa7dd656d487b",
        "f486f8528292c067620e9d495f66b0af2ad55dd4dc2e9d35b11aa7dd656d487c"
    ],
    "source_aarch64": [
        "filex"
    ],
    "sha256sums_aarch64": [
        "1f72deec0a9af5059e1350d7b5a5a93bc4d2fbef6eeaa363fda764eb9c472b7b"
    ],
    "source_armv7h": [
        "filey"
    ],
    "sha256sums_armv7h": [
        "8229b4bbf43563d8b688d19a514fb0fa0a1ef0eadbd96233882a4b496fa4c8c8"
    ]
}
"""


def test_srcinfo_parse() -> None:
    (info, error) = parse.parse_srcinfo(SRCINFO)

    assert not error

    # Check if parsing function returns what we expect
    assert json.loads(EXPECTED) == info


def test_git_update_extract_arch_fields() -> None:
    (info, error) = parse.parse_srcinfo(SRCINFO)

    assert not error

    # check arrays
    sources = extract_arch_fields(info, "source")

    # We expect 7 source files
    assert len(sources) == 7

    # First one should be our service file
    assert sources[0]["value"] == "ponies.service"

    # add more...
