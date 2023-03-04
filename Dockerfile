# syntax=docker/dockerfile:1.3
FROM ubuntu:lunar AS prod

ENV FINBOT_ROOT_DIR="/finbot"
ENV PYTHONPATH="${FINBOT_ROOT_DIR}:${PYTHONPATH}"
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y \
        git \
        libgconf-2-4 \
        libpq-dev \
        python3-pip \
        python3.11 \
        python3.11-dev \
        xvfb && \
    python3.11 -m pip install --upgrade pip && \
    python3.11 -m pip install --no-cache-dir playwright && \
    playwright install chromium --with-deps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR ${FINBOT_ROOT_DIR}

COPY requirements.txt .

RUN python3.11 -m pip install --upgrade --no-cache-dir -r requirements.txt

COPY . .

FROM prod AS dev

RUN apt-get update && \
    apt-get install -y \
        inotify-tools \
        postgresql-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN python3.11 -m pip install --no-cache-dir -r requirements-dev.txt && \
    python3.11 -m pip install --no-cache-dir pip-tools
