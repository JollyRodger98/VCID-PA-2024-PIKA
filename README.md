# PIKA app

## Production

### Docker Compose
Create an `.env` file with the following content:
```
ELASTIC_PASSWORD=Tim123456
KIBANA_PASSWORD=Tim123456
STACK_VERSION=8.13.3
CLUSTER_NAME=docker-cluster
LICENSE=basic
ES_PORT=9200
KIBANA_PORT=5601
MEM_LIMIT=1073741824
```

The contents of the .env file should be copied as they are. Passwords may be changed if desired.

__Warning__: On some Platforms the command `sudo sysctl -w vm.max_map_count=262144` needs to be executed for the elastic cluster to run correctly.

Run the following `docker compose` command to start all docker containers for production.

```shell
docker compose \
  --file compose.yaml \
  --file docker/compose.production.yaml \
  --project-name pika \
  up \
  --detach
    
```

To test the docker compose deployment, replace `compose.production.yml` with `compose.development.yml`. This binds the
PIKA app port locally to 8000 instead of to post 80 on a specified IP address.

## Development

### Python

Create a python development environment.

1. Create virtual environment:
    ```shell
    python -m venv .venv
    ```
2. Activate environment
    ```shell
   # MacOS
    source .venv/bin/activate
    ```
   
   ```shell
   # Windows
   .\.venv\Scripts\activate
   ```
3. Install packages
    ```shell
    pip install -e .[dev]
    ```

### Docker

Commands needed to start Docker containers for development.

Create network first:

```shell
docker network create dev-pika
```

### MySQL

Start MySQL database container. To initiate emtpy database omit the `dump.sql` line

```shell
# MacOS
docker run \
  --name dev-mysql \
  --publish 3306:3306 \
  --volume dev_mysql_data:/var/lib/mysql \
  --volume ./pika_dbs.sql:/docker-entrypoint-initdb.d/dump.sql \
  --env MYSQL_ROOT_PASSWORD=Tim123456 \
  --network dev-pika \
  --rm \
  --detach \
  mysql:latest
```

```shell
# Windows
docker run --name dev-mysql --publish 3306:3306 --volume dev_mysql_data:/var/lib/mysql --volume $PWD/pika_dbs.sql:/docker-entrypoint-initdb.d/dump.sql --env MYSQL_ROOT_PASSWORD=Tim123456 --network dev-pika --rm --detach mysql:latest
```
#### MySQL Dump

Dump MySQL databases `pika` and `pika_library` into `pika_dbs.sql`.

```shell
docker exec dev-mysql mysqldump -uroot -pTim123456 --databases pika > pika_dbs.sql
```

This file is used when initiating the development or production databases. Edit the `docker run` command or the `compose.yml` file to initiate an empty database.

### Elastic

Start a single node Elasticsearch cluster.

```shell
# MacOS
docker run \
  --name dev-elastic \
  --publish 9200:9200 \
  --publish 9300:9300 \
  --env discovery.type=single-node \
  --env ELASTIC_PASSWORD=Tim123456 \
  --network dev-pika \
  --rm \
  --detach \
  docker.elastic.co/elasticsearch/elasticsearch:8.13.3
```

```shell
# Windows
docker run --name dev-elastic --publish 9200:9200 --publish 9300:9300 --env discovery.type=single-node --env ELASTIC_PASSWORD=Tim123456 --network dev-pika --rm --detach docker.elastic.co/elasticsearch/elasticsearch:8.13.3
```

Copy elastic certificate for local use.

```shell
docker cp dev-elastic:/usr/share/elasticsearch/config/certs/http_ca.crt .
```

Test connection:

```shell
curl https://localhost:9200 --cacert ./http_ca.crt --user elastic:Tim123456
```

### Babel

Babel uses translations files to make different languages available.

Extract all strings:

```shell
pybabel extract -F babel.cfg -k _l -o messages.pot .
```

Initiate language files. This example initiates German.

```shell
pybabel init -i messages.pot -d app/translations -l de
```

If the file is alredy initiated, use the following command to update the files.

```shell
pybabel update -i messages.pot -d pika/translations
```

Compile for flask:

```shell
pybabel compile -d pika/translations
```
