# finbot

## Developer guide

### Getting started

#### 1. Build all containers

```bash
(host) $ docker-compose build
```

#### 2. Start the database (finbotdb) and the development containers

```bash
(host) $ docker-compose up -d finbotdb dev
```

#### 3. Get shell in dev container

```bash
(host) $ docker exec -it dev /bin/bash
```

#### 4. Initialize vault

This step creates a `.secure/secret.txt` file (readable by user only) 
containing a key used to encrypt/decrypt local account credentials.

```bash
(dev ) $ make init-vault
```

#### 5. Create development account

This step creates a default development account file that is then encrypted and
placed in the vault. The default account file only contains 'dummy' account
entries.

```bash
(dev ) $ make init-account
(dev ) $ make edit-account # optional, see below
```

Additional accounts can be registered in the development account file if needed.
The list of available providers is available in `finbot/providers`.

#### 6. Initial development environment test (optional)

A basic test can be run to make sure the development environment is setup 
properly.

```bash
(dev ) $ make test-providers
```

#### 7. Initialize the database (finbotdb)

```bash
(dev ) $ make finbotdb-build # create all tables based on finbot sqlalchemy model
(dev ) $ make finbotdb-hydrate # adds minimal configuration needed for finbot to work
(dev ) $ make finbotdb-add-account # persist the development account created previously in the database
```

#### 8. Start the finbot backend

```bash
(dev ) $ exit # leave the development docker container
(host) $ docker-compose up # start all remaining web services (-d to start in deamon mode)
```

The web application will be available at `127.0.0.1:5005` as soon as this message
is displayed by the `webapp` container (it can take a few minutes to start):

```
webapp        | Compiled successfully!
webapp        | 
webapp        | You can now view webapp in the browser.
webapp        | 
webapp        |   Local:            http://localhost:5005/
webapp        |   On Your Network:  http://192.168.32.7:5005/
```

Services and applications will automatically be restarted whenever a code change
is made to any of the files under `finbot/` or `webapp/`.
