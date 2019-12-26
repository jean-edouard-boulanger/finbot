FROM ubuntu:latest

RUN apt-get upgrade

RUN apt-get update

RUN apt-get install -y \
    python3.7 \
    python3.7-dev \
    python3-pip \
    libpq-dev

RUN python3.7 -m pip install --upgrade pip

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.2.1/wait /usr/bin/wait
RUN chmod +x /usr/bin/wait

RUN pip3 install \
    flask \
    requests \
    cryptography \
    cffi \
    psycopg2 \
    sqlalchemy \
    pytz


