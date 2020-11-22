FROM ubuntu:latest

ENV TZ=Europe/Paris
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get upgrade

RUN apt-get update

RUN apt-get install -y \
    python3.9 \
    python3.9-dev \
    python3-pip \
    libpq-dev

RUN python3.9 -m pip install --upgrade pip

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.2.1/wait /usr/bin/wait
RUN chmod +x /usr/bin/wait

RUN pip3 install \
    requests \
    psycopg2 \
    sqlalchemy \
    pytz \
    stackprinter

