#==============================================================================
# Multi-stage build for a React (Vite) app.
#
# Stage 1 "build"  : full Node toolchain — installs ~200 MB of node_modules and
#                    compiles the app into a folder of static files.
# Stage 2 (final)  : plain nginx. It copies ONLY the compiled /app/dist folder.
#                    Node, npm and node_modules never reach the final image.
#
# Result: ~50 MB instead of ~450 MB, and no build tooling in production.
#==============================================================================

# ----- Stage 1: build -----
FROM node:20-alpine AS build

WORKDIR /app

# Copy only the manifests first so `npm ci` is cached until dependencies change.
COPY package*.json ./
RUN npm install

# Now the source. Editing a component invalidates only this layer, not the install.
COPY . .

# Produces /app/dist — index.html plus hashed JS/CSS bundles.
RUN npm run build

# ----- Stage 2: serve -----
FROM nginx:alpine

# Take the built artifacts out of the build stage.
COPY --from=build /app/dist /usr/share/nginx/html

# SPA-aware config: unknown paths fall back to index.html so client-side
# routing works on a hard refresh instead of returning 404.
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
