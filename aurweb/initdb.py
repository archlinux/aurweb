import aurweb.db
import aurweb.schema

import argparse
import sqlalchemy


def feed_initial_data(conn):
    conn.execute(aurweb.schema.AccountTypes.insert(), [
        {'ID': 1, 'AccountType': 'User'},
        {'ID': 2, 'AccountType': 'Trusted User'},
        {'ID': 3, 'AccountType': 'Developer'},
        {'ID': 4, 'AccountType': 'Trusted User & Developer'},
    ])
    conn.execute(aurweb.schema.DependencyTypes.insert(), [
        {'ID': 1, 'Name': 'depends'},
        {'ID': 2, 'Name': 'makedepends'},
        {'ID': 3, 'Name': 'checkdepends'},
        {'ID': 4, 'Name': 'optdepends'},
    ])
    conn.execute(aurweb.schema.RelationTypes.insert(), [
        {'ID': 1, 'Name': 'conflicts'},
        {'ID': 2, 'Name': 'provides'},
        {'ID': 3, 'Name': 'replaces'},
    ])
    conn.execute(aurweb.schema.RequestTypes.insert(), [
        {'ID': 1, 'Name': 'deletion'},
        {'ID': 2, 'Name': 'orphan'},
        {'ID': 3, 'Name': 'merge'},
    ])


def run(args):
    engine = sqlalchemy.create_engine(aurweb.db.get_sqlalchemy_url(),
                                      echo=(args.verbose >= 1))
    aurweb.schema.metadata.create_all(engine)
    feed_initial_data(engine.connect())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='python -m aurweb.initdb',
        description='Initialize the aurweb database.')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='increase verbosity')
    args = parser.parse_args()
    run(args)
