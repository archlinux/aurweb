from http import HTTPStatus

from aurweb.templates import make_context, render_template


async def not_found(request, exc):
    context = make_context(request, "Page Not Found")
    return render_template(request, "errors/404.html", context,
                           HTTPStatus.NOT_FOUND)


async def service_unavailable(request, exc):
    context = make_context(request, "Service Unavailable")
    return render_template(request, "errors/503.html", context,
                           HTTPStatus.SERVICE_UNAVAILABLE)

# Maps HTTP errors to functions
exceptions = {
    404: not_found,
    503: service_unavailable
}
