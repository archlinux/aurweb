#!/usr/bin/env python3

import re

import pyalpm

from sqlalchemy import and_

import aurweb.config

from aurweb import db, util
from aurweb.models import OfficialProvider


def _main(force: bool = False):
    blacklist = set()
    providers = set()
    repomap = dict()

    db_path = aurweb.config.get("aurblup", "db-path")
    sync_dbs = aurweb.config.get('aurblup', 'sync-dbs').split(' ')
    server = aurweb.config.get('aurblup', 'server')

    h = pyalpm.Handle("/", db_path)
    for sync_db in sync_dbs:
        repo = h.register_syncdb(sync_db, pyalpm.SIG_DATABASE_OPTIONAL)
        repo.servers = [server.replace("%s", sync_db)]
        t = h.init_transaction()
        repo.update(force)
        t.release()

        for pkg in repo.pkgcache:
            blacklist.add(pkg.name)
            util.apply_all(pkg.replaces, blacklist.add)
            providers.add((pkg.name, pkg.name))
            repomap[(pkg.name, pkg.name)] = repo.name
            for provision in pkg.provides:
                provisionname = re.sub(r'(<|=|>).*', '', provision)
                providers.add((pkg.name, provisionname))
                repomap[(pkg.name, provisionname)] = repo.name

    with db.begin():
        old_providers = set(
            db.query(OfficialProvider).with_entities(
                OfficialProvider.Name.label("Name"),
                OfficialProvider.Provides.label("Provides")
            ).distinct().order_by("Name").all()
        )

        for name, provides in old_providers.difference(providers):
            db.delete_all(db.query(OfficialProvider).filter(
                and_(OfficialProvider.Name == name,
                     OfficialProvider.Provides == provides)
            ))

        for name, provides in providers.difference(old_providers):
            repo = repomap.get((name, provides))
            db.create(OfficialProvider, Name=name,
                      Repo=repo, Provides=provides)


def main(force: bool = False):
    db.get_engine()
    _main(force)


if __name__ == '__main__':
    main()
