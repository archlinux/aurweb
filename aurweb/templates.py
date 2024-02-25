import copy
import functools
import os
from http import HTTPStatus
from typing import Callable

import jinja2
from fastapi import Request
from fastapi.responses import HTMLResponse

import aurweb.config
from aurweb import l10n, time

# Prepare jinja2 objects.
_loader = jinja2.FileSystemLoader(
    os.path.join(aurweb.config.get("options", "aurwebdir"), "templates")
)
_env = jinja2.Environment(
    loader=_loader, autoescape=True, extensions=["jinja2.ext.i18n"]
)

DEFAULT_TIMEZONE = aurweb.config.get("options", "default_timezone")


def register_filter(name: str) -> Callable:
    """A decorator that can be used to register a filter.

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

        _env.filters[name] = wrapper
        return wrapper

    return decorator


def register_function(name: str) -> Callable:
    """A decorator that can be used to register a function."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        if name in _env.globals:
            raise KeyError(f"Jinja already has a function named '{name}'")
        _env.globals[name] = wrapper
        return wrapper

    return decorator


def make_context(request: Request, title: str, next: str = None):
    """Create a context for a jinja2 TemplateResponse."""
    import aurweb.auth.creds

    commit_url = aurweb.config.get_with_fallback("devel", "commit_url", None)
    commit_hash = aurweb.config.get_with_fallback("devel", "commit_hash", None)
    max_chars_comment = aurweb.config.getint("options", "max_chars_comment", 5000)
    if commit_hash:
        # Shorten commit_hash to a short Git hash.
        commit_hash = commit_hash[:7]

    timezone = time.get_request_timezone(request)
    language = l10n.get_request_language(request)
    return {
        "request": request,
        "commit_url": commit_url,
        "commit_hash": commit_hash,
        "language": language,
        "languages": l10n.SUPPORTED_LANGUAGES,
        "rtl": language in l10n.RIGHT_TO_LEFT_LANGUAGES,
        "timezone": timezone,
        "timezones": time.SUPPORTED_TIMEZONES,
        "title": title,
        "now": time.now(timezone),
        "utcnow": time.utcnow(),
        "config": aurweb.config,
        "creds": aurweb.auth.creds,
        "next": next if next else request.url.path,
        "version": os.environ.get("COMMIT_HASH", aurweb.config.AURWEB_VERSION),
        "max_chars_comment": max_chars_comment,
    }


async def make_variable_context(request: Request, title: str, next: str = None):
    """Make a context with variables provided by the user
    (query params via GET or form data via POST)."""
    context = make_context(request, title, next)
    to_copy = (
        dict(request.query_params)
        if request.method.lower() == "get"
        else dict(await request.form())
    )

    for k, v in to_copy.items():
        if k not in context:
            context[k] = v
    context["q"] = dict(request.query_params)

    return context


def base_template(path: str):
    templates = copy.copy(_env)
    return templates.get_template(path)


def render_raw_template(request: Request, path: str, context: dict):
    """Render a Jinja2 multi-lingual template with some context."""
    # Create a deep copy of our jinja2 _environment. The _environment in
    # total by itself is 48 bytes large (according to sys.getsizeof).
    # This is done so we can install gettext translations on the template
    # _environment being rendered without installing them into a global
    # which is reused in this function.
    templates = copy.copy(_env)

    translator = l10n.get_raw_translator_for_request(context.get("request"))
    templates.install_gettext_translations(translator)

    template = templates.get_template(path)
    return template.render(context)


def render_template(
    request: Request, path: str, context: dict, status_code: HTTPStatus = HTTPStatus.OK
):
    """Render a template as an HTMLResponse."""
    rendered = render_raw_template(request, path, context)
    return HTMLResponse(rendered, status_code=int(status_code))
