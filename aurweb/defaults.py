""" Constant default values centralized in one place. """

# Default [O]ffset
O = 0

# Default [P]er [P]age
PP = 50

# Default Comments Per Page
COMMENTS_PER_PAGE = 10

# A whitelist of valid PP values
PP_WHITELIST = {50, 100, 250}

# Default `by` parameter for RPC search.
RPC_SEARCH_BY = "name-desc"


def fallback_pp(per_page: int) -> int:
    """If `per_page` is a valid value in PP_WHITELIST, return it.
    Otherwise, return defaults.PP."""
    if per_page not in PP_WHITELIST:
        return PP
    return per_page
