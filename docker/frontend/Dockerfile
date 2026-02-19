FROM node:20-alpine AS builder
WORKDIR /build

COPY canteen-analysis-system10.10.6/vite-project/package*.json ./
RUN npm install --no-audit --no-fund

COPY canteen-analysis-system10.10.6/vite-project ./
RUN npm run build

FROM nginx:1.27-alpine
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /build/dist /usr/share/nginx/html

EXPOSE 80
