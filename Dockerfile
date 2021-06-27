FROM archlinux:base-devel
ENV PYTHONPATH=/aurweb
ENV AUR_CONFIG=conf/config

# Setup some default system stuff.
RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime

RUN mkdir -p .pkg-cache

# Install dependencies.
RUN pacman -Syu --noconfirm --noprogressbar \
    --cachedir .pkg-cache git gpgme protobuf pyalpm \
    python-mysqlclient python-pygit2 python-srcinfo python-bleach \
    python-markdown python-sqlalchemy python-alembic python-pytest \
    python-werkzeug python-pytest-tap python-fastapi nginx python-authlib \
    python-itsdangerous python-httpx python-jinja python-pytest-cov \
    python-requests python-aiofiles python-python-multipart \
    python-pytest-asyncio python-coverage hypercorn python-bcrypt \
    python-email-validator openssh python-lxml mariadb mariadb-libs \
    python-isort flake8 cgit uwsgi uwsgi-plugin-cgi php php-fpm \
    python-asgiref uvicorn python-pip python-wheel

RUN useradd -U -d /aurweb -c 'AUR User' aur

COPY docker /docker

WORKDIR /aurweb
COPY . .

RUN make -C po all install
RUN pip3 install -t /aurweb/app --upgrade -I .

# Set permissions on directories and binaries.
RUN bash -c 'find /aurweb/app -type d -exec chmod 755 {} \;'
RUN chmod 755 /aurweb/app/bin/*
