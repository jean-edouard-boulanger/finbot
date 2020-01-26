# finbot

open-source personal financial data aggregation framework / platform.

## Developer guide

### 1. Development environment setup

A local development environment can be created by running the following command:

```bash
(host) $ make init-dev
```

This command can be re-executed at any point. **Word of caution**, the existing
database will be erased and initialized with the local development account.

### 2. Useful commands

#### Containers management

The entire `finbot` infrastructure can be run locally (as long as dependencies 
are available) but `Docker` and `docker-compose` is the preferred development
environment.

At this point, each application has its own docker container which provides their
respective runtime environment. The overall infrastructure orchestration is 
defined in `docker-compose.yml`. The development setup allows to make modifications
while running the finbot infrastructure, at which point applications are automatically
restarted.

- **Build all containers**: `docker-compose build`
- **Start all containers**: `docker-compose up` or `docker-compose up -d` to run as daemon.
- **Stop all containers**: `docker-compose down`

### 3. `finbot` application layout

#### `finbot/` directory

`finbot` Backend implementation (Python):

- `apps/`: Backend applications (_web servers, scheduler_)
- `clients/`: Python clients given access to backend servers.
- `core/`: General-purpose packages (_high-level utilities, etc._)
- `model/__init__.py`: `finbot` `SQLAlchemy` business model (_used to create finbotdb schema_)
- `providers/`: Implement the `finbot.providers.Base`. Each module gives access to
   a specific financial data provider (most are implemented via Selenium, but some
   rely on specific APIs, like Kraken or Google sheets)

#### `webapp/` directory

`finbot` web application implementation, based on React.