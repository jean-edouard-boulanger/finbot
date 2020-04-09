FROM ubuntu:latest

RUN apt-get upgrade

RUN apt-get update

RUN apt-get install -y \
    python3.7 \
    python3.7-dev \
    python3-pip \
    libpq-dev

RUN python3.7 -m pip install --upgrade pip

RUN pip3 install \
    jsonschema \
    requests \
    cryptography \
    cffi \
    flask \
    flask-cors \
    flask-jwt-extended \
    psycopg2 \
    sqlalchemy \
    pytz \
    stackprinter

