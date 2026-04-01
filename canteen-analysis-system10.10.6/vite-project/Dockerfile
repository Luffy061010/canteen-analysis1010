FROM node:20-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN set -eux; \
		npm config set registry https://registry.npmmirror.com; \
		ok=0; \
		for i in 1 2 3; do \
			if [ -f package-lock.json ]; then \
				npm ci --include=dev --no-audit --no-fund; \
			else \
				npm install --include=dev --no-audit --no-fund; \
			fi; \
			if [ -x node_modules/.bin/vite ]; then \
				ok=1; \
				break; \
			fi; \
			echo "npm deps incomplete, retrying... ($i/3)"; \
			rm -rf node_modules; \
			sleep 8; \
		done; \
		if [ "$ok" -ne 1 ]; then \
			echo "vite dependency missing after retries"; \
			exit 1; \
		fi

COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
