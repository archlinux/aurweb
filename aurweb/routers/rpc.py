import hashlib

from http import HTTPStatus
from typing import List, Optional
from urllib.parse import unquote

import orjson

from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import JSONResponse

from aurweb import defaults
from aurweb.ratelimit import check_ratelimit
from aurweb.rpc import RPC

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


@router.get("/rpc")
async def rpc(request: Request,
              v: Optional[int] = Query(default=None),
              type: Optional[str] = Query(default=None),
              by: Optional[str] = Query(default=defaults.RPC_SEARCH_BY),
              arg: Optional[str] = Query(default=None),
              args: Optional[List[str]] = Query(default=[], alias="arg[]")):

    # Create a handle to our RPC class.
    rpc = RPC(version=v, type=type)

    # If ratelimit was exceeded, return a 429 Too Many Requests.
    if check_ratelimit(request):
        return JSONResponse(rpc.error("Rate limit reached"),
                            status_code=int(HTTPStatus.TOO_MANY_REQUESTS))

    # Prepare list of arguments for input. If 'arg' was given, it'll
    # be a list with one element.
    arguments = parse_args(request)
    data = rpc.handle(by=by, args=arguments)

    # Serialize `data` into JSON in a sorted fashion. This way, our
    # ETag header produced below will never end up changed.
    output = orjson.dumps(data, option=orjson.OPT_SORT_KEYS)

    # Produce an md5 hash based on `output`.
    md5 = hashlib.md5()
    md5.update(output)
    etag = md5.hexdigest()

    # Finally, return our JSONResponse with the ETag header.
    # The ETag header expects quotes to surround any identifier.
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/ETag
    return Response(output.decode(), headers={
        "Content-Type": "application/json",
        "ETag": f'"{etag}"'
    })
