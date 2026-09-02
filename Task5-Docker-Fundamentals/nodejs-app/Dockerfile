# Alpine variant: ~50 MB instead of ~350 MB for the full Debian-based image.
FROM node:20-alpine

# Everything after this happens in /app inside the container.
WORKDIR /app

# Copy package.json FIRST and install separately from the source code.
# Docker caches each layer; as long as package.json is unchanged, the slow
# npm install layer is reused even when server.js changes.
COPY package.json ./
RUN npm install --omit=dev

# Now copy the application source.
COPY server.js ./

# Documentation only — it does not publish the port. `docker run -p` does that.
EXPOSE 3000

# Run as a non-root user. The node image ships a `node` user for exactly this.
USER node

# Exec form (JSON array): node becomes PID 1 and receives SIGTERM directly,
# so `docker stop` shuts down cleanly instead of waiting 10 s for a SIGKILL.
CMD ["node", "server.js"]
