include .env

CONFIG_PATH = /src/migrations/alembic.ini

.PHONY: seed-db-and-up
seed-db-and-up:
	$(MAKE) database-up
	$(MAKE) migrations-upgrade
	$(MAKE) seed-db
	$(MAKE) bot-up

.PHONY: bot-up
bot-up:
	docker compose up -d bot_container

##3 database ###
.PHONY: database-shell
database-shell:
	docker compose exec -it postgres_container psql \
		-U $(POSTGRES_USER) \
		-d $(POSTGRES_DB)

.PHONY: database-up
database-up:
	docker compose up -d postgres_container

.PHONY: restart
restart:
	$(MAKE) database-up
	docker compose exec -T postgres_container psql \
		-U $(POSTGRES_USER) \
		-d $(POSTGRES_DB) \
		-c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	$(MAKE) migrations-upgrade

.PHONY: seed-db
seed-db:
	POSTGRES_HOST=localhost python -m src.json2database_runner

.PHONY: database-cli-rw
database-cli-rw:
	PGUSER=${POSTGRES_USER} \
	PGPASSWORD=${POSTGRES_PASSWORD_RW} \
	PGHOST=localhost \
	PGPORT=${POSTGRES_PORT} \
	PGDATABASE=${POSTGRES_DB} \
	pgcli

.PHONY: database-cli-ro
database-cli-ro:
	PGUSER=readonly_user \
	PGPASSWORD=${POSTGRES_PASSWORD_RO} \
	PGHOST=localhost \
	PGPORT=${POSTGRES_PORT} \
	PGDATABASE=${POSTGRES_DB} \
	pgcli

### migrations ###
.PHONY: migrations-help
migrations-help:
	docker compose run --rm alembic_container uv run alembic --help

.PHONY: migrations-revision
migrations-revision:
	docker compose run --rm alembic_container \
		alembic -c $(CONFIG_PATH) revision -m "$(msg)"

.PHONY: migrations-revision-autogenerate
migrations-revision-autogenerate:
	docker compose run --rm alembic_container \
		alembic -c $(CONFIG_PATH) revision --autogenerate -m "$(msg)"

.PHONY: migrations-upgrade
migrations-upgrade:
	docker compose run --rm alembic_container \
		alembic -c $(CONFIG_PATH) upgrade head

.PHONY: migrations-current
migrations-current:
	docker compose run --rm alembic_container \
		alembic -c $(CONFIG_PATH) current

.PHONY: migrations-downgrade
migrations-downgrade:
	docker compose run --rm alembic_container \
		alembic -c $(CONFIG_PATH) downgrade -1

.PHONY: migrations-downgrade-base
migrations-downgrade-base:
	docker compose run --rm alembic_container \
		alembic -c $(CONFIG_PATH) downgrade base
