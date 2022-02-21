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
docker compose build aurweb-image
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
