FROM nginx:alpine

# Nginx's default DocumentRoot inside this image.
COPY index.html /usr/share/nginx/html/index.html

# Drop in a server block. Anything in /etc/nginx/conf.d/*.conf is included by
# the main nginx.conf, so this replaces the image's default site.
COPY default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# The base image's CMD is ["nginx", "-g", "daemon off;"].
# `daemon off;` keeps nginx in the foreground so the container stays alive.
