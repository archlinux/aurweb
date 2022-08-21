"""
API routers for FastAPI.

See https://fastapi.tiangolo.com/tutorial/bigger-applications/
"""
from . import (
    accounts,
    auth,
    html,
    packages,
    pkgbase,
    requests,
    rpc,
    rss,
    sso,
    trusted_user,
)

"""
aurweb application routes. This constant can be any iterable
and each element must have a .router attribute which points
to a fastapi.APIRouter.
"""
APP_ROUTES = [
    accounts,
    auth,
    html,
    packages,
    pkgbase,
    requests,
    trusted_user,
    rss,
    rpc,
    sso,
]
