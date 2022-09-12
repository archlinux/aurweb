FROM archlinux:base-devel

VOLUME /root/.cache/pypoetry/cache
VOLUME /root/.cache/pypoetry/artifacts
VOLUME /root/.cache/pre-commit

ENV PATH="/root/.poetry/bin:${PATH}"
ENV PYTHONPATH=/aurweb
ENV AUR_CONFIG=conf/config
ENV COMPOSE=1

# Install system-wide dependencies.
COPY ./docker/scripts/install-deps.sh /install-deps.sh
RUN /install-deps.sh

# Copy Docker scripts
COPY ./docker /docker
COPY ./docker/scripts/* /usr/local/bin/


# Copy over all aurweb files.
COPY . /aurweb

# Working directory is aurweb root @ /aurweb.
WORKDIR /aurweb

# Copy initial config to conf/config.
RUN cp -vf conf/config.dev conf/config
RUN sed -i "s;YOUR_AUR_ROOT;/aurweb;g" conf/config

# Install Python dependencies.
RUN /docker/scripts/install-python-deps.sh compose

# Compile asciidocs.
RUN make -C doc

# Add our aur user.
RUN useradd -U -d /aurweb -c 'AUR User' aur

# Setup some default system stuff.
RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime

# Install translations.
RUN make -C po all install

# Install pre-commit repositories and run lint check.
RUN pre-commit run -a
