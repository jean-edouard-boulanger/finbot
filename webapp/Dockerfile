FROM node:22-alpine AS builder

WORKDIR /workspace

COPY package*.json ./

RUN npm install

COPY public/ ./public/
COPY src/ ./src/
COPY index.html ./
COPY vite.config.ts ./
COPY tailwind.config.ts ./
COPY postcss.config.js ./
COPY tsconfig.json ./
COPY tsconfig.node.json ./

RUN npm run build

FROM nginx:1.23-alpine

COPY --from=builder /workspace/dist /usr/share/nginx/html/finbot/

RUN rm -rf /etc/nginx/conf.d/*
COPY docker/nginx/* /etc/nginx/conf.d/

CMD ["nginx", "-g", "daemon off;"]
