import logging
import logging.config

import sqlalchemy

from alembic import context

import aurweb.db
import aurweb.schema

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# model MetaData for autogenerating migrations
target_metadata = aurweb.schema.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# If configure_logger is either True or not specified,
# configure the logger via fileConfig.
if config.attributes.get("configure_logger", True):
    logging.config.fileConfig(config.config_file_name)

# This grabs the root logger in env.py.
logger = logging.getLogger(__name__)


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    dbname = aurweb.db.name()
    logging.info(f"Performing offline migration on database '{dbname}'.")
    context.configure(
        url=aurweb.db.get_sqlalchemy_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    dbname = aurweb.db.name()
    logging.info(f"Performing online migration on database '{dbname}'.")
    connectable = sqlalchemy.create_engine(
        aurweb.db.get_sqlalchemy_url(),
        poolclass=sqlalchemy.pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
