import aurweb.config


class User:
    """ A fake User model. """
    # Fake columns.
    LangPreference = aurweb.config.get("options", "default_lang")

    # A fake authenticated flag.
    authenticated = False

    def is_authenticated(self):
        return self.authenticated


class Client:
    """ A fake FastAPI Request.client object. """
    # A fake host.
    host = "127.0.0.1"


class Request:
    """ A fake Request object which mimics a FastAPI Request for tests. """
    client = Client()
    cookies = dict()
    headers = dict()
    user = User()
