#!/usr/bin/env python3

from sqlalchemy import update

from aurweb import db, time
from aurweb.models import User


def _main():
    limit_to = time.utcnow() - 86400 * 7

    update_ = update(User).where(
        User.LastLogin < limit_to
    ).values(LastLoginIPAddress=None)
    db.get_session().execute(update_)

    update_ = update(User).where(
        User.LastSSHLogin < limit_to
    ).values(LastSSHLoginIPAddress=None)
    db.get_session().execute(update_)


def main():
    db.get_engine()
    with db.begin():
        _main()


if __name__ == '__main__':
    main()
