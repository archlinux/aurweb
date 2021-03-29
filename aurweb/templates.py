import copy
import os

from datetime import datetime
from http import HTTPStatus

import jinja2

from fastapi import Request
from fastapi.responses import HTMLResponse

import aurweb.config

from aurweb import l10n

# Prepare jinja2 objects.
loader = jinja2.FileSystemLoader(os.path.join(
    aurweb.config.get("options", "aurwebdir"), "templates"))
env = jinja2.Environment(loader=loader, autoescape=True,
                         extensions=["jinja2.ext.i18n"])

# Add tr translation filter.
env.filters["tr"] = l10n.tr


def make_context(request: Request, title: str, next: str = None):
    """ Create a context for a jinja2 TemplateResponse. """

    return {
        "request": request,
        "language": l10n.get_request_language(request),
        "languages": l10n.SUPPORTED_LANGUAGES,
        "title": title,
        # The 'now' context variable will not show proper datetimes
        # until we've implemented timezone support here.
        "now": datetime.now(),
        "config": aurweb.config,
        "next": next if next else request.url.path
    }


def render_template(path: str, context: dict, status_code=int(HTTPStatus.OK)):
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
    return HTMLResponse(rendered, status_code=status_code)
