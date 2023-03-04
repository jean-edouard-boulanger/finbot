FROM node:19-alpine

WORKDIR /finbot

COPY package*.json ./

RUN npm install

COPY . .

RUN npx browserslist@latest --update-db && npm run build
