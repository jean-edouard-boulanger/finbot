# syntax=docker/dockerfile:1.3
FROM python:3.11-bullseye AS builder

ENV VENV_DIR="/venv"
ENV PATH="${VENV_DIR}/bin:${PATH}"
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y libgconf-2-4 libpq-dev

RUN python3.11 -m venv ${VENV_DIR}

COPY requirements.txt .

RUN python3.11 -m pip install --upgrade --no-cache-dir -r requirements.txt

FROM python:3.11-slim-bullseye AS runtime

ENV FINBOT_ROOT_DIR="/finbot"
ENV VENV_DIR="/venv"
ENV PYTHONPATH="${FINBOT_ROOT_DIR}:${PYTHONPATH}"
ENV PATH="${VENV_DIR}/bin:${PATH}"
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y xvfb && \
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

FROM runtime AS runtime-playwright

RUN playwright install chromium --with-deps && apt-get clean

FROM runtime-playwright AS runtime-dev

RUN apt-get update && \
    apt-get install -y \
      git \
      make \
      inotify-tools \
      postgresql-client && \
    apt-get clean

COPY requirements-dev.txt .

RUN python3.11 -m pip install --no-cache-dir -r requirements-dev.txt && \
    python3.11 -m pip install --no-cache-dir pip-tools
