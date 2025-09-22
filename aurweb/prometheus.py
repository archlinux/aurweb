from typing import Any, Callable, Optional

from prometheus_client import Counter, Gauge
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_fastapi_instrumentator.metrics import Info
from starlette.routing import Match, Route

from aurweb import aur_logging

logger = aur_logging.get_logger(__name__)
_instrumentator = Instrumentator()


# Custom metrics
SEARCH_REQUESTS = Counter(
    "aur_search_requests", "Number of search requests by cache hit/miss", ["cache"]
)
USERS = Gauge(
    "aur_users", "Number of AUR users by type", ["type"], multiprocess_mode="livemax"
)
PACKAGES = Gauge(
    "aur_packages",
    "Number of AUR packages by state",
    ["state"],
    multiprocess_mode="livemax",
)
REQUESTS = Gauge(
    "aur_requests",
    "Number of AUR requests by type and status",
    ["type", "status"],
    multiprocess_mode="livemax",
)


def instrumentator():
    return _instrumentator


# FastAPI metrics
# Taken from https://github.com/stephenhillier/starlette_exporter
# Their license is included in LICENSES/starlette_exporter.
# The code has been modified to remove child route checks
# (since we don't have any) and to stay within an 80-width limit.
def get_matching_route_path(
    scope: dict[Any, Any], routes: list[Route], route_name: Optional[str] = None
) -> str:
    """
    Find a matching route and return its original path string

    Will attempt to enter mounted routes and subrouters.

    Credit to https://github.com/elastic/apm-agent-python

    """
    for route in routes:
        match, child_scope = route.matches(scope)
        if match == Match.FULL:
            route_name = route.path

            """
            # This path exists in the original function's code, but we
            # don't need it (currently), so it's been removed to avoid
            # useless test coverage.
            child_scope = {**scope, **child_scope}
            if isinstance(route, Mount) and route.routes:
                child_route_name = get_matching_route_path(child_scope,
                                                           route.routes,
                                                           route_name)
                if child_route_name is None:
                    route_name = None
                else:
                    route_name += child_route_name
            """

            return route_name
        elif match == Match.PARTIAL and route_name is None:
            route_name = route.path


def http_requests_total() -> Callable[[Info], None]:
    metric = Counter(
        "http_requests_total",
        "Number of HTTP requests.",
        labelnames=("method", "path", "status"),
    )

    def instrumentation(info: Info) -> None:
        if info.request.method.lower() in ("head", "options"):  # pragma: no cover
            return

        scope = info.request.scope

        # Taken from https://github.com/stephenhillier/starlette_exporter
        # Their license is included at LICENSES/starlette_exporter.
        # The code has been slightly modified: we no longer catch
        # exceptions; we expect this collector to always succeed.
        # Failures in this collector shall cause test failures.
        if not (scope.get("endpoint", None) and scope.get("router", None)):
            return None

        root_path = scope.get("root_path", str())
        app = scope.get("app", {})

        if hasattr(app, "root_path"):
            app_root_path = getattr(app, "root_path")
            if root_path.startswith(app_root_path):
                root_path = root_path[len(app_root_path) :]

        base_scope = {
            "type": scope.get("type"),
            "path": root_path + scope.get("path"),
            "path_params": scope.get("path_params", {}),
            "method": scope.get("method"),
        }

        method = scope.get("method")
        path = get_matching_route_path(base_scope, scope.get("router").routes)

        if info.response:
            status = str(int(info.response.status_code))[:1] + "xx"
            metric.labels(method=method, path=path, status=status).inc()

    return instrumentation


def http_api_requests_total() -> Callable[[Info], None]:
    metric = Counter(
        "http_api_requests",
        "Number of times an RPC API type has been requested.",
        labelnames=("type", "status"),
    )

    def instrumentation(info: Info) -> None:
        if info.request.method.lower() in ("head", "options"):  # pragma: no cover
            return

        if info.request.url.path.rstrip("/") == "/rpc":
            type = info.request.query_params.get("type", "None")
            if info.response:
                status = str(info.response.status_code)[:1] + "xx"
                metric.labels(type=type, status=status).inc()

    return instrumentation
