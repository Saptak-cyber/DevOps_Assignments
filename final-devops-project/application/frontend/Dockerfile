# syntax=docker/dockerfile:1
# ---------- stage 1: build the static bundle with Node ----------
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY index.html vite.config.js ./
COPY public ./public
COPY src ./src
RUN npm run build

# ---------- stage 2: serve it with unprivileged nginx (uid 101, port 8080) ----------
FROM nginxinc/nginx-unprivileged:1.30-alpine-slim AS runtime
LABEL org.opencontainers.image.title="clinicdesk-frontend" \
      org.opencontainers.image.description="ClinicDesk React UI served by nginx" \
      org.opencontainers.image.source="https://github.com/Saptak-cyber/DevOps_Assignments"
ENV BACKEND_UPSTREAM=backend:8000
COPY --chown=root:root nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --chown=root:root --from=build /app/dist /usr/share/nginx/html
USER 101
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1
