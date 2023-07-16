FROM node:19-alpine as builder

WORKDIR /workspace

COPY package*.json ./

RUN npm install --omit=dev

COPY public/ ./public/
COPY src/ ./src/
COPY tsconfig.json ./

RUN npx browserslist@latest --update-db && npm run build

FROM nginx:1.23-alpine

COPY --from=builder /workspace/build /usr/share/nginx/html/finbot/

RUN rm -rf /etc/nginx/conf.d/*
COPY docker/nginx/* /etc/nginx/conf.d/

CMD ["nginx", "-g", "daemon off;"]
