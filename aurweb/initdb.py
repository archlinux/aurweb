import argparse

import alembic.command
import alembic.config
import sqlalchemy

import aurweb.db
import aurweb.schema


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
    # Ensure Alembic is fine before we do the real work, in order not to fail at
    # the last step and leave the database in an inconsistent state. The
    # configuration is loaded lazily, so we query it to force its loading.
    if args.use_alembic:
        alembic_config = alembic.config.Config('alembic.ini')
        alembic_config.get_main_option('script_location')
        alembic_config.attributes["configure_logger"] = False

    engine = sqlalchemy.create_engine(aurweb.db.get_sqlalchemy_url(),
                                      echo=(args.verbose >= 1))
    aurweb.schema.metadata.create_all(engine)
    feed_initial_data(engine.connect())

    if args.use_alembic:
        alembic.command.stamp(alembic_config, 'head')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='python -m aurweb.initdb',
        description='Initialize the aurweb database.')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='increase verbosity')
    parser.add_argument('--no-alembic',
                        help='disable Alembic migrations support',
                        dest='use_alembic', action='store_false')
    args = parser.parse_args()
    run(args)
