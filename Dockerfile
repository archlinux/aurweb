FROM archlinux:base-devel

ENV PYTHONPATH=/aurweb
ENV AUR_CONFIG=conf/config

# Copy Docker scripts
COPY ./docker /docker
COPY ./docker/scripts/*.sh /usr/local/bin/

# Copy over all aurweb files.
COPY . /aurweb

# Working directory is aurweb root @ /aurweb.
WORKDIR /aurweb

# Install dependencies
RUN docker/scripts/install-deps.sh
RUN pip install -r requirements.txt

# Add our aur user.
RUN useradd -U -d /aurweb -c 'AUR User' aur

# Setup some default system stuff.
RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime

# Install translations.
RUN make -C po all install

# Install package and scripts.
RUN python setup.py install --install-scripts=/usr/local/bin
