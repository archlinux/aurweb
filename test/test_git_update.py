from typing import Any

import pytest

from aurweb.git.update_common import size_humanize
from aurweb.git.update_legacy import parse_dep


@pytest.mark.parametrize(
    "size, expected",
    [
        (1024, "1024B"),
        (1024.5, "1024.50B"),
        (256000, "250.00KiB"),
        (25600000, "24.41MiB"),
        (2560000000, "2.38GiB"),
        (2560000000000, "2.33TiB"),
        (2560000000000000, "2.27PiB"),
        (2560000000000000000, "2.22EiB"),
        (2560000000000000000000, "2.17ZiB"),
        (2560000000000000000000000, "2.12YiB"),
    ],
)
def test_size_humanize(size: Any, expected: str) -> None:
    assert size_humanize(size) == expected


@pytest.mark.parametrize(
    "depstring, exp_depname, exp_depdesc, exp_depcond",
    [
        (
            "my-little-pony: optional kids support",
            "my-little-pony",
            "optional kids support",
            "",
        ),
        (
            "my-little-pony>7",
            "my-little-pony",
            "",
            ">7",
        ),
        (
            "my-little-pony=7",
            "my-little-pony",
            "",
            "=7",
        ),
        (
            "my-little-pony<7",
            "my-little-pony",
            "",
            "<7",
        ),
        (
            "my-little-pony<=7",
            "my-little-pony",
            "",
            "<=7",
        ),
        (
            "my-little-pony>=7.1: optional kids support",
            "my-little-pony",
            "optional kids support",
            ">=7.1",
        ),
    ],
)
def test_parse_dep(
    depstring: str, exp_depname: str, exp_depdesc: str, exp_depcond: str
) -> None:
    depname, depdesc, depcond = parse_dep(depstring)
    assert depname == exp_depname
    assert depdesc == exp_depdesc
    assert depcond == exp_depcond
