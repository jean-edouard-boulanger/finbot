FROM ubuntu:latest

RUN apt-get update

RUN apt-get install -y \
    curl \
    python3.9 \
    python3.9-dev \
    python3-pip \
    unzip \
    vim \
    less \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    postgresql-client \
    libpq-dev

RUN python3.9 -m pip install --upgrade pip

RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add && \
    echo "deb [arch=amd64]  http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
    apt-get -y update && \
    apt-get -y install google-chrome-stable

RUN wget -O /tmp/chromedriver_linux64.zip https://chromedriver.storage.googleapis.com/2.41/chromedriver_linux64.zip && \
    cd /tmp && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/bin/chromedriver && \
    chown root:root /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver

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
    alembic \
    pytz \
    selenium \
    terminaltables \
    price-parser \
    krakenex \
    python-bittrex \
    python-binance \
    pycoingecko \
    gspread \
    oauth2client \
    pandas \
    schedule \
    stackprinter

