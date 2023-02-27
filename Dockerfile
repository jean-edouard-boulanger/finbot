# syntax=docker/dockerfile:1.3
FROM ubuntu:latest

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get install -y \
        inotify-tools \
        libgconf-2-4 \
        libpq-dev \
        postgresql-client \
        python3-pip \
        python3.11 \
        python3.11-dev \
        xvfb && \
    python3.11 -m pip install --upgrade pip && \
    python3.11 -m pip install --no-cache-dir playwright && \
    playwright install chromium --with-deps && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /finbot

COPY requirements.txt .

RUN python3.11 -m pip install --no-cache-dir -r requirements.txt
