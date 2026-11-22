FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json pnpm-workspace.yaml* ./
COPY packages/shared/package.json ./packages/shared/
COPY apps/web/package.json ./apps/web/

RUN npm install -g pnpm && pnpm install --frozen-lockfile || npm install

COPY packages/shared ./packages/shared
COPY apps/web ./apps/web

RUN npm --prefix packages/shared run build || true
RUN npm --prefix apps/web run build

FROM nginx:alpine
COPY --from=builder /app/apps/web/dist /usr/share/nginx/html
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf 2>/dev/null || true
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]

