FROM ubuntu:latest

RUN apt-get upgrade

RUN apt-get update

RUN apt-get install -y \
    python3.9 \
    python3.9-dev \
    python3-pip \
    libpq-dev

RUN python3.9 -m pip install --upgrade pip

RUN pip3 install \
    jsonschema \
    flask \
    requests \
    cryptography \
    cffi \
    psycopg2 \
    sqlalchemy \
    pytz \
    pandas \
    stackprinter

