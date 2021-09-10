from typing import Any, Dict

import paginate

from jinja2 import pass_context

from aurweb import config, util
from aurweb.templates import register_filter, register_function


@register_filter("pager_nav")
@pass_context
def pager_nav(context: Dict[str, Any],
              page: int, total: int, prefix: str) -> str:
    page = int(page)  # Make sure this is an int.

    pp = context.get("PP", 50)

    # Setup a local query string dict, optionally passed by caller.
    q = context.get("q", dict())

    search_by = context.get("SeB", None)
    if search_by:
        q["SeB"] = search_by

    sort_by = context.get("SB", None)
    if sort_by:
        q["SB"] = sort_by

    def create_url(page: int):
        nonlocal q
        offset = max(page * pp - pp, 0)
        qs = util.to_qs(util.extend_query(q, ["O", offset]))
        return f"{prefix}?{qs}"

    # Use the paginate module to produce our linkage.
    pager = paginate.Page([], page=page + 1,
                          items_per_page=pp,
                          item_count=total,
                          url_maker=create_url)

    return pager.pager(
        link_attr={"class": "page"},
        curpage_attr={"class": "page"},
        separator="&nbsp",
        format="$link_first $link_previous ~5~ $link_next $link_last",
        symbol_first="« First",
        symbol_previous="‹ Previous",
        symbol_next="Next ›",
        symbol_last="Last »")


@register_function("config_getint")
def config_getint(section: str, key: str) -> int:
    return config.getint(section, key)


@register_function("round")
def do_round(f: float) -> int:
    return round(f)
