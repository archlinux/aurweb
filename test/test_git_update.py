from typing import Any

import pytest
from alpm.alpm_types import ALPMError, OptionalDependency, relation_or_soname_from_str

from aurweb.git.update import (
    GenericRelation,
    sql_rel_description,
    sql_rel_name,
    sql_rel_requirement,
)
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
        # An alpm-sonamev1 (see https://alpm.archlinux.page/specifications/alpm-sonamev1.7.html).
        # basic
        (
            "libfoo.so",
            "libfoo.so",
            "",
            "",
        ),
        # explicit
        (
            "libfoo.so=1-64",
            "libfoo.so",
            "",
            "=1-64",
        ),
        # unversioned
        (
            "libfoo.so=libfoo.so-64",
            "libfoo.so",
            "",
            "=libfoo.so-64",
        ),
        # Edge case:
        # Dependency on a soname described as normal package relation (e.g. paru
        # dependency on libalpm.so>=14). These are "valid" package relations but do not
        # make sense as version requirements towards a soname, as sonames require a
        # strict (equals to) relation for a consumer to be able to use them.
        # See also: https://alpm.archlinux.page/specifications/alpm-package-relation.7.html
        (
            "libfoo.so>=4",
            "libfoo.so",
            "",
            ">=4",
        ),
        # An alpm-sonamev2 (see https://alpm.archlinux.page/specifications/alpm-sonamev2.7.html).
        (
            "lib:libfoo.so.1",
            "lib:libfoo.so.1",
            "",
            "",
        ),
    ],
)
@pytest.mark.parametrize("alpm_parser", [True, False])
def test_parse_dep(
    depstring: str,
    exp_depname: str,
    exp_depdesc: str,
    exp_depcond: str,
    alpm_parser: bool,
) -> None:
    if alpm_parser:
        try:
            relation: GenericRelation = relation_or_soname_from_str(depstring)
        except ALPMError:
            relation: GenericRelation = OptionalDependency.from_str(depstring)
        assert sql_rel_name(relation) == exp_depname
        assert sql_rel_description(relation) == exp_depdesc
        assert sql_rel_requirement(relation) == exp_depcond
    else:
        depname, depdesc, depcond = parse_dep(depstring)
        assert depname == exp_depname
        assert depdesc == exp_depdesc
        assert depcond == exp_depcond
