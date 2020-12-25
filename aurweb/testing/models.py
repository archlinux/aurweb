import warnings

from sqlalchemy import exc

import aurweb.db


def make_user(**kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", exc.SAWarning)
        from aurweb.models.user import User
        user = User(**kwargs)
        aurweb.db.session.add(user)
        aurweb.db.session.commit()
        return user


def make_session(**kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", exc.SAWarning)
        from aurweb.models.session import Session
        session = Session(**kwargs)
        aurweb.db.session.add(session)
        aurweb.db.session.commit()
        return session
