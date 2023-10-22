export FINBOT_EDIT_CMD ?= code --wait
export BLACK_SETTINGS = --exclude 'migrations/|webapp/|venv/' .
export ISORT_SETTINGS = --profile black finbot/ tools/
export PYTHONPATH := ${PWD}:${PYTHONPATH}

alembic-gen:
	tools/check-env.sh message;
	docker-compose run --rm operator bash -c 'env FINBOT_WAIT_DEPS=finbotdb ./tools/finbot-wait && alembic revision -m "${message}"'

alembic-upgrade:
	docker-compose run --rm operator bash -c 'env FINBOT_WAIT_DEPS=finbotdb ./tools/finbot-wait && alembic upgrade head'

alembic-downgrade:
	docker-compose run --rm operator bash -c 'env FINBOT_WAIT_DEPS=finbotdb ./tools/finbot-wait && alembic downgrade -1'

alembic-history:
	docker-compose run --rm operator bash -c 'env FINBOT_WAIT_DEPS=finbotdb ./tools/finbot-wait && alembic history'

pip-compile-all:
	./tools/pip-compile-all

docker-build-webapp:
	cd webapp && docker build -t finbotapp/webapp:latest -f Dockerfile --pull .

docker-build-runtime:
	docker build --target runtime -t finbotapp/runtime:latest -f Dockerfile --pull .

docker-build-runtime-playwright:
	docker build --target runtime-playwright -t finbotapp/runtime-playwright:latest -f Dockerfile --pull .

docker-build-runtime-dev:
	docker build --target runtime-dev -t finbotapp/runtime-dev:latest -f Dockerfile --pull .

docker-build-prod: docker-build-runtime docker-build-runtime-playwright docker-build-webapp
docker-build-dev: docker-build-runtime-dev
docker-build-all: docker-build-dev docker-build-prod

trigger-valuation:
	tools/check-env.sh accounts;
	docker-compose exec schedsrv \
		./tools/run -- python3.12 finbot/apps/schedsrv/schedsrv.py \
			--mode one_shot \
			--accounts ${accounts}

run-system-tests:
	docker-compose run --rm operator env FINBOT_WAIT_DEPS=appwsrv,finbotwsrv ./tools/finbot-wait;
	docker-compose run --rm operator python3.12 -m pytest tests/system/

finbotdb-build:
	python3.12 tools/finbotdb build

finbotdb-destroy:
	python3.12 tools/finbotdb destroy

finbotdb-rebuild:
	python3.12 tools/finbotdb destroy && \
	python3.12 tools/finbotdb build

finbotdb-hydrate:
	python3.12 tools/finbotdb hydrate \
		--data-file ./tools/hydrate.json

finbotdb-psql:
	docker compose exec finbotdb psql -U finbot

init-dev:
	tools/init-dev.sh

py-unit-tests:
	python3.12 -m pytest tests/unit

prettier-ts:
	cd webapp && npm run prettier

tsc-build-check:
	cd webapp && npm run tsc-build-check

prettier-check-ts:
	cd webapp && npm run prettier-check

eslint:
	cd webapp && npm run lint-check:prod

banned-keywords-check-ts:
	tools/banned-keywords.py --source-dirs webapp/src

ruff:
	python3.12 -m ruff .

version-bump-check:
	tools/versioning check-version-bump

black-check:
	python3.12 -m black --check $(BLACK_SETTINGS)

black:
	python3.12 -m black $(BLACK_SETTINGS)

isort-check:
	python3.12 -m isort --check $(ISORT_SETTINGS)

isort:
	python3.12 -m isort $(ISORT_SETTINGS)

mypy:
	python3.12 -m mypy --strict finbot/

unit-tests-py:
	python3.12 -m pytest -vv tests/unit

unit-tests: unit-tests-py

banned-keywords-check-py:
	tools/banned-keywords.py --source-dirs finbot

lint-sh:
	grep -rl '^#!/.*bash' --exclude-dir=webapp --exclude-dir='./.*' . |\
 		xargs shellcheck -e SC1090 -e SC1091 -e SC2002 -S style

lint-schema:
	docker-compose run --rm operator ./tools/lint-schema.py

generate-ts-client:
	docker-compose run --rm operator ./tools/generate-ts-client

lint-py: mypy ruff black-check isort-check banned-keywords-check-py unit-tests-py
lint-ts: eslint tsc-build-check prettier-check-ts banned-keywords-check-ts
lint-all: lint-py lint-ts lint-sh

format-py: black isort
format-ts: prettier-ts
format-all: format-py format-ts
