# Aurweb and Docker

The `INSTALL` document details a manual Aurweb setup, but Docker images are also
provided here to avoid the complications of database configuration (and so
forth).

### Setup

Naturally, both `docker` and `docker-compose` must be installed, and your Docker
service must be started:

```sh
systemctl start docker.service
```

The main image - `aurweb` - must be built manually:

```sh
docker compose build
```

### Starting and Stopping the Services

With the above steps complete, you can bring up an initial cluster:

```sh
docker compose up
```

Subsequent runs will be done with `start` instead of `up`. The cluster can be
stopped with `docker compose stop`.

### Testing

With a running cluster, execute the following in a new terminal:

```sh
docker compose run test
```

### Generating Dummy Data

Before you can make meaningful queries to the cluster, it needs some data.
Luckily such data can be generated.

```sh
docker compose exec fastapi /bin/bash
pacman -S words fortune-mod
./schema/gendummydata.py dummy.sql
mysql aurweb < dummy.sql
```

The generation script may prompt you to install other Arch packages before it
can proceed.

### Querying the RPC

The Fast (Python) API runs on Port 8444, while the legacy PHP version runs
on 8443. You can query one like so:

```sh
curl -k "https://localhost:8444/rpc/?v=5&type=search&arg=python"
```

`-k` bypasses local certificate issues that `curl` will otherwise complain about.
