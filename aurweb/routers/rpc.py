import hashlib
import re

from http import HTTPStatus
from typing import List, Optional
from urllib.parse import unquote

import orjson

from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import JSONResponse

from aurweb import defaults
from aurweb.ratelimit import check_ratelimit
from aurweb.rpc import RPC, documentation

router = APIRouter()


def parse_args(request: Request):
    """ Handle legacy logic of 'arg' and 'arg[]' query parameter handling.

    When 'arg' appears as the last argument given to the query string,
    that argument is used by itself as one single argument, regardless
    of any more 'arg' or 'arg[]' parameters supplied before it.

    When 'arg[]' appears as the last argument given to the query string,
    we iterate from last to first and build a list of arguments until
    we hit an 'arg'.

    TODO: This handling should be addressed in v6 of the RPC API. This
    was most likely a bi-product of legacy handling of versions 1-4
    which we no longer support.

    :param request: FastAPI request
    :returns: List of deduced arguments
    """
    # Create a list of (key, value) pairs of the given 'arg' and 'arg[]'
    # query parameters from last to first.
    query = list(reversed(unquote(request.url.query).split("&")))
    parts = [
        e.split("=", 1) for e in query if e.startswith(("arg=", "arg[]="))
    ]

    args = []
    if parts:
        # If we found 'arg' and/or 'arg[]' arguments, we begin processing
        # the set of arguments depending on the last key found.
        last = parts[0][0]

        if last == "arg":
            # If the last key was 'arg', then it is our sole argument.
            args.append(parts[0][1])
        else:
            # Otherwise, it must be 'arg[]', so traverse backward
            # until we reach a non-'arg[]' key.
            for key, value in parts:
                if key != last:
                    break
                args.append(value)

    return args


JSONP_EXPR = re.compile(r'^[a-zA-Z0-9()_.]{1,128}$')


@router.get("/rpc/")
@router.get("/rpc")
async def rpc(request: Request,
              v: Optional[int] = Query(default=None),
              type: Optional[str] = Query(default=None),
              by: Optional[str] = Query(default=defaults.RPC_SEARCH_BY),
              arg: Optional[str] = Query(default=None),
              args: Optional[List[str]] = Query(default=[], alias="arg[]"),
              callback: Optional[str] = Query(default=None)):

    if not request.url.query:
        return documentation()

    # Create a handle to our RPC class.
    rpc = RPC(version=v, type=type)

    # If ratelimit was exceeded, return a 429 Too Many Requests.
    if check_ratelimit(request):
        return JSONResponse(rpc.error("Rate limit reached"),
                            status_code=int(HTTPStatus.TOO_MANY_REQUESTS))

    # If `callback` was provided, produce a text/javascript response
    # valid for the jsonp callback. Otherwise, by default, return
    # application/json containing `output`.
    content_type = "application/json"
    if callback:
        if not re.match(JSONP_EXPR, callback):
            return rpc.error("Invalid callback name.")

        content_type = "text/javascript"

    # Prepare list of arguments for input. If 'arg' was given, it'll
    # be a list with one element.
    arguments = parse_args(request)
    data = rpc.handle(by=by, args=arguments)

    # Serialize `data` into JSON in a sorted fashion. This way, our
    # ETag header produced below will never end up changed.
    content = orjson.dumps(data, option=orjson.OPT_SORT_KEYS)

    # Produce an md5 hash based on `output`.
    md5 = hashlib.md5()
    md5.update(content)
    etag = md5.hexdigest()

    # The ETag header expects quotes to surround any identifier.
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/ETag
    headers = {
        "Content-Type": content_type,
        "ETag": f'"{etag}"'
    }

    if_none_match = request.headers.get("If-None-Match", str())
    if if_none_match and if_none_match.strip("\t\n\r\" ") == etag:
        return Response(headers=headers,
                        status_code=int(HTTPStatus.NOT_MODIFIED))

    if callback:
        content = f"/**/{callback}({content.decode()})"

    return Response(content, headers=headers)
