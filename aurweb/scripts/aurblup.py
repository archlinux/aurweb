#!/usr/bin/env python3

import pyalpm
import re

import aurweb.config
import aurweb.db

db_path = aurweb.config.get('aurblup', 'db-path')
sync_dbs = aurweb.config.get('aurblup', 'sync-dbs').split(' ')
server = aurweb.config.get('aurblup', 'server')


def main():
    blacklist = set()
    providers = set()
    repomap = dict()

    h = pyalpm.Handle("/", db_path)
    for sync_db in sync_dbs:
        repo = h.register_syncdb(sync_db, pyalpm.SIG_DATABASE_OPTIONAL)
        repo.servers = [server.replace("%s", sync_db)]
        t = h.init_transaction()
        repo.update(False)
        t.release()

        for pkg in repo.pkgcache:
            blacklist.add(pkg.name)
            [blacklist.add(x) for x in pkg.replaces]
            providers.add((pkg.name, pkg.name))
            repomap[(pkg.name, pkg.name)] = repo.name
            for provision in pkg.provides:
                provisionname = re.sub(r'(<|=|>).*', '', provision)
                providers.add((pkg.name, provisionname))
                repomap[(pkg.name, provisionname)] = repo.name

    conn = aurweb.db.Connection()

    cur = conn.execute("SELECT Name, Provides FROM OfficialProviders")
    oldproviders = set(cur.fetchall())

    for pkg, provides in providers.difference(oldproviders):
        repo = repomap[(pkg, provides)]
        conn.execute("INSERT INTO OfficialProviders (Name, Repo, Provides) "
                     "VALUES (?, ?, ?)", [pkg, repo, provides])
    for pkg, provides in oldproviders.difference(providers):
        conn.execute("DELETE FROM OfficialProviders "
                     "WHERE Name = ? AND Provides = ?", [pkg, provides])

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
