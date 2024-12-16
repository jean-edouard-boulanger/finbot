export FINBOT_EDIT_CMD ?= code --wait
export PYTHONPATH := ${PWD}:${PYTHONPATH}

docker_exec := docker compose exec operator
ifneq (,$(wildcard /.dockerenv))
	docker_exec :=
endif

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
	$(docker_exec) \
		./tools/run -- python3.12 finbot/apps/schedsrv/schedsrv.py \
			--mode one_shot \
			--accounts ${accounts}

run-system-tests:
	$(docker_exec) env FINBOT_WAIT_DEPS=appwsrv,finbotwsrv ./tools/finbot-wait && \
		$(docker_exec) python3.12 -m pytest tests/system/

finbotdb-build:
	$(docker_exec) python3.12 tools/finbotdb build

finbotdb-destroy:
	$(docker_exec) python3.12 tools/finbotdb destroy

finbotdb-rebuild:
	$(docker_exec) python3.12 tools/finbotdb destroy && \
		python3.12 tools/finbotdb build

finbotdb-hydrate:
	$(docker_exec) python3.12 tools/finbotdb hydrate \
		--data-file ./tools/hydrate.json

finbotdb-psql:
	docker compose exec finbotdb psql -U finbot

finbotdb-migrate:
	tools/check-env.sh message;
	$(docker_exec) bash -c 'env FINBOT_WAIT_DEPS=finbotdb ./tools/finbot-wait && alembic revision -m "${message}"'

finbotdb-upgrade:
	$(docker_exec) bash -c 'env FINBOT_WAIT_DEPS=finbotdb ./tools/finbot-wait && alembic upgrade head'

finbotdb-downgrade:
	$(docker_exec) bash -c 'env FINBOT_WAIT_DEPS=finbotdb ./tools/finbot-wait && alembic downgrade head-1'

finbotdb-history:
	$(docker_exec) bash -c 'env FINBOT_WAIT_DEPS=finbotdb ./tools/finbot-wait && alembic history'

finbotdb-heads:
	$(docker_exec) bash -c 'env FINBOT_WAIT_DEPS=finbotdb ./tools/finbot-wait && alembic heads'

init-dev:
	tools/init-dev.sh

prettier-ts:
	cd webapp && npm run prettier

tsc-build-check:
	cd webapp && npm run tsc-build-check

prettier-check-ts:
	cd webapp && npm run prettier-check

eslint:
	cd webapp && npm run lint-check:prod

banned-keywords-check-ts:
	$(docker_exec) tools/banned-keywords.py --source-dirs webapp/src

flakes-check:
	$(docker_exec) python3.12 -m ruff check --ignore I

flakes:
	$(docker_exec) python3.12 -m ruff check --ignore I --fix

version-bump-check:
	$(docker_exec) tools/versioning check-version-bump

black-check:
	$(docker_exec) python3.12 -m ruff format --check

black:
	$(docker_exec) python3.12 -m ruff format

isort-check:
	$(docker_exec) python3.12 -m ruff check --select I

isort:
	$(docker_exec) python3.12 -m ruff check --select I --fix

mypy:
	$(docker_exec) python3.12 -m mypy --strict finbot/

unit-tests-py:
	$(docker_exec) python3.12 -m pytest -vv tests/unit

unit-tests: unit-tests-py

banned-keywords-check-py:
	$(docker_exec) tools/banned-keywords.py --source-dirs finbot

lint-sh:
	$(docker_exec) grep -rl '^#!/.*bash' --exclude-dir=webapp --exclude-dir='./.*' --exclude-dir='venv' . |\
 		xargs shellcheck -e SC1090 -e SC1091 -e SC2002 -S style

lint-schema:
	$(docker_exec) ./tools/lint-schema.py

generate-ts-client:
	$(docker_exec) ./tools/generate-ts-client

shell:
	$(docker_exec) bash

lint-py: mypy flakes-check black-check isort-check banned-keywords-check-py unit-tests-py
lint-ts: eslint tsc-build-check prettier-check-ts banned-keywords-check-ts
lint-all: lint-py lint-ts lint-sh

format-py: black isort
format-ts: prettier-ts
format-all: format-py format-ts
