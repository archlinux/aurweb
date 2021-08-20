import copy
import functools
import os
import zoneinfo

from datetime import datetime
from http import HTTPStatus
from typing import Callable
from urllib.parse import quote_plus

import jinja2

from fastapi import Request
from fastapi.responses import HTMLResponse

import aurweb.config

from aurweb import captcha, l10n, time, util

# Prepare jinja2 objects.
loader = jinja2.FileSystemLoader(os.path.join(
    aurweb.config.get("options", "aurwebdir"), "templates"))
env = jinja2.Environment(loader=loader, autoescape=True,
                         extensions=["jinja2.ext.i18n"])

# Add t{r,n} translation filters.
env.filters["tr"] = l10n.tr
env.filters["tn"] = l10n.tn

# Utility filters.
env.filters["dt"] = util.timestamp_to_datetime
env.filters["as_timezone"] = util.as_timezone
env.filters["dedupe_qs"] = util.dedupe_qs
env.filters["urlencode"] = quote_plus
env.filters["get_vote"] = util.get_vote
env.filters["number_format"] = util.number_format

# Add captcha filters.
env.filters["captcha_salt"] = captcha.captcha_salt_filter
env.filters["captcha_cmdline"] = captcha.captcha_cmdline_filter

# Add account utility filters.
env.filters["account_url"] = util.account_url


def register_filter(name: str) -> Callable:
    """ A decorator that can be used to register a filter.

    Example
        @register_filter("some_filter")
        def some_filter(some_value: str) -> str:
            return some_value.replace("-", "_")

    Jinja2
        {{ 'blah-blah' | some_filter }}

    :param name: Filter name
    :return: Callable used for filter
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        if name in env.filters:
            raise KeyError(f"Jinja already has a filter named '{name}'")
        env.filters[name] = wrapper
        return wrapper
    return decorator


def make_context(request: Request, title: str, next: str = None):
    """ Create a context for a jinja2 TemplateResponse. """

    timezone = time.get_request_timezone(request)
    return {
        "request": request,
        "language": l10n.get_request_language(request),
        "languages": l10n.SUPPORTED_LANGUAGES,
        "timezone": timezone,
        "timezones": time.SUPPORTED_TIMEZONES,
        "title": title,
        "now": datetime.now(tz=zoneinfo.ZoneInfo(timezone)),
        "config": aurweb.config,
        "next": next if next else request.url.path
    }


async def make_variable_context(request: Request, title: str, next: str = None):
    """ Make a context with variables provided by the user
    (query params via GET or form data via POST). """
    context = make_context(request, title, next)
    to_copy = dict(request.query_params) \
        if request.method.lower() == "get" \
        else dict(await request.form())

    for k, v in to_copy.items():
        context[k] = v

    return context


def render_template(request: Request,
                    path: str,
                    context: dict,
                    status_code: HTTPStatus = HTTPStatus.OK):
    """ Render a Jinja2 multi-lingual template with some context. """

    # Create a deep copy of our jinja2 environment. The environment in
    # total by itself is 48 bytes large (according to sys.getsizeof).
    # This is done so we can install gettext translations on the template
    # environment being rendered without installing them into a global
    # which is reused in this function.
    templates = copy.copy(env)

    translator = l10n.get_raw_translator_for_request(context.get("request"))
    templates.install_gettext_translations(translator)

    template = templates.get_template(path)
    rendered = template.render(context)

    response = HTMLResponse(rendered, status_code=status_code)
    secure_cookies = aurweb.config.getboolean("options", "disable_http_login")
    response.set_cookie("AURLANG", context.get("language"),
                        secure=secure_cookies, httponly=True)
    response.set_cookie("AURTZ", context.get("timezone"),
                        secure=secure_cookies, httponly=True)
    return util.add_samesite_fields(response, "strict")
