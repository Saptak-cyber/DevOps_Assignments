# ---------- Stage 1: install dependencies ----------
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
# --omit=dev drops devDependencies; --ignore-scripts blocks arbitrary
# postinstall scripts from packages, which is a supply-chain safety measure.
RUN npm install --omit=dev --ignore-scripts

# ---------- Stage 2: runtime ----------
FROM node:20-alpine
WORKDIR /app

# Only the resolved node_modules tree comes across — no npm cache,
# no build tooling, no lockfile churn.
COPY --from=deps /app/node_modules ./node_modules
COPY package.json server.js ./

ENV NODE_ENV=production PORT=3000
EXPOSE 3000
USER node

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://127.0.0.1:3000/health',r=>process.exit(r.statusCode===200?0:1)).on('error',()=>process.exit(1))"

CMD ["node", "server.js"]
