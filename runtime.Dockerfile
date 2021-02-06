FROM ubuntu:latest

ENV TZ=Europe/Paris

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && \
    apt-get install -y \
        inotify-tools \
        libgconf-2-4 \
        libpq-dev \
        postgresql-client \
        python3-pip \
        python3.9 \
        python3.9-dev

WORKDIR /finbot

COPY requirements.txt .

RUN python3.9 -m pip install --upgrade pip && \
    python3.9 -m pip install -r requirements.txt
