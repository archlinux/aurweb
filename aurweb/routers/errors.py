from aurweb.templates import make_context, render_template
from aurweb import l10n


async def not_found(request, exc):
    _ = l10n.get_translator_for_request(request)
    context = make_context(request, f"404 - {_('Page Not Found')}")
    return render_template("errors/404.html", context)


async def service_unavailable(request, exc):
    _ = l10n.get_translator_for_request(request)
    context = make_context(request, "503 - {_('Service Unavailable')}")
    return render_template("errors/503.html", context)

# Maps HTTP errors to functions
exceptions = {
    404: not_found,
    503: service_unavailable
}
