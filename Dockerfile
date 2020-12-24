FROM archlinux
COPY . /aurweb
WORKDIR /aurweb

# Install dependencies.
RUN pacman -Syu --noconfirm base-devel git gpgme protobuf pyalpm \
    python-mysql-connector python-pygit2 python-srcinfo python-bleach \
    python-markdown python-sqlalchemy python-alembic python-pytest \
    python-werkzeug python-pytest-tap python-fastapi nginx python-authlib \
    python-itsdangerous python-httpx python-jinja python-pytest-cov \
    python-requests python-aiofiles python-python-multipart \
    python-pytest-asyncio python-coverage hypercorn

# Remove aurweb.sqlite3 if it was copied over via COPY.
RUN rm -fv aurweb.sqlite3

# Setup our test config.
RUN sed -r "s;YOUR_AUR_ROOT;/aurweb;g" conf/config.dev > conf/config

# Install translations.
RUN AUR_CONFIG=conf/config make -C po all install

# Initialize the database.
RUN AUR_CONFIG=conf/config python -m aurweb.initdb

# Test everything!
RUN make -C test

# Produce a coverage report.
RUN coverage report --include='aurweb/*'
