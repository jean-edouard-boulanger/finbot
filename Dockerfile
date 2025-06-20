# syntax=docker/dockerfile:1.3
FROM python:3.13-bullseye AS builder

ENV VENV_DIR="/venv"
ENV PATH="${VENV_DIR}/bin:${PATH}"
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y libgconf-2-4 libpq-dev wget

ADD https://astral.sh/uv/install.sh /uv-installer.sh

RUN env XDG_BIN_HOME=/usr/local/bin sh /uv-installer.sh && rm -f /uv-installer.sh

COPY requirements.txt .

RUN uv venv ${VENV_DIR} \
    && uv pip install -r requirements.txt

FROM python:3.13-slim-bullseye AS runtime

ENV FINBOT_ROOT_DIR="/finbot"
ENV VENV_DIR="/venv"
ENV PYTHONPATH="${FINBOT_ROOT_DIR}:${PYTHONPATH}"
ENV PATH="${VENV_DIR}/bin:${PATH}"
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y xvfb gnupg && \
    apt-get clean

COPY --from=builder ${VENV_DIR} ${VENV_DIR}
COPY --from=builder /usr/lib/x86_64-linux-gnu/libpq* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libldap* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/liblber* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libsasl* /usr/lib/x86_64-linux-gnu/

WORKDIR ${FINBOT_ROOT_DIR}

COPY finbot/ finbot/
COPY migrations/ migrations/
COPY tools/ tools/
COPY alembic.ini finbotctl Makefile ./
COPY envs/temporal/dynamicconfig /etc/temporal/config/dynamicconfig

FROM runtime AS runtime-playwright

RUN playwright install chromium --with-deps && apt-get clean

FROM runtime-playwright AS runtime-dev

RUN apt-get update && \
    apt-get install -y \
      default-jre \
      git \
      make \
      inotify-tools \
      libpq-dev \
      nodejs \
      npm \
      postgresql-client && \
    apt-get clean

COPY requirements-dev.txt .

COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

RUN uv pip install -r requirements-dev.txt && \
    echo "installing openapi-generator-cli" && \
    npm install @openapitools/openapi-generator-cli@2.7.0 -g && \
    echo "downloading pinned openapi-generator-cli version" && \
    openapi-generator-cli version  # downloads the openapi-generator-cli version specified in openapitools.json
