import aurweb.config


class User:
    """A fake User model."""

    # Fake columns.
    LangPreference = aurweb.config.get("options", "default_lang")
    Timezone = aurweb.config.get("options", "default_timezone")

    # A fake authenticated flag.
    authenticated = False

    def is_authenticated(self):
        return self.authenticated


class Client:
    """A fake FastAPI Request.client object."""

    # A fake host.
    host = "127.0.0.1"


class URL:
    path: str

    def __init__(self, path: str = "/"):
        self.path = path


class Request:
    """A fake Request object which mimics a FastAPI Request for tests."""

    client = Client()
    url = URL()

    def __init__(
        self,
        user: User = User(),
        authenticated: bool = False,
        method: str = "GET",
        headers: dict[str, str] = dict(),
        cookies: dict[str, str] = dict(),
        url: str = "/",
        query_params: dict[str, str] = dict(),
    ) -> None:
        self.user = user
        self.user.authenticated = authenticated

        self.method = method.upper()
        self.headers = headers
        self.cookies = cookies
        self.url = URL(path=url)
        self.query_params = query_params
