FROM archlinux:base-devel

ENV PYTHONPATH=/aurweb
ENV AUR_CONFIG=conf/config

# Copy our single bootstrap script.
COPY docker/scripts/install-deps.sh /install-deps.sh
RUN /install-deps.sh

# Add our aur user.
RUN useradd -U -d /aurweb -c 'AUR User' aur

# Setup some default system stuff.
RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime

# Copy the rest of docker.
COPY ./docker /docker
COPY ./docker/scripts/*.sh /usr/local/bin/

# Copy from host to container.
COPY . /aurweb

# Working directory is aurweb root @ /aurweb.
WORKDIR /aurweb

# Install translations.
RUN make -C po all install

# Install package and scripts.
RUN python setup.py install --install-scripts=/usr/local/bin
