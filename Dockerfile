FROM archlinux:base-devel

VOLUME /root/.cache/pypoetry/cache
VOLUME /root/.cache/pypoetry/artifacts

ENV PATH="/root/.poetry/bin:${PATH}"
ENV PYTHONPATH=/aurweb
ENV AUR_CONFIG=conf/config

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

# Install Python dependencies.
RUN /docker/scripts/install-python-deps.sh

# Add our aur user.
RUN useradd -U -d /aurweb -c 'AUR User' aur

# Setup some default system stuff.
RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime

# Install translations.
RUN make -C po all install
