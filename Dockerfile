FROM ubuntu:latest

RUN apt-get upgrade

RUN apt-get update

RUN apt-get install -y \
    curl \
    python3.7 \
    python3-pip \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4

RUN python3.7 -m pip install --upgrade pip

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

COPY requirements.txt /tmp/requirements.txt

RUN pip3 install -r /tmp/requirements.txt
