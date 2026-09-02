# The official Apache HTTP Server image. Its DocumentRoot is /usr/local/apache2/htdocs/
FROM httpd:2.4-alpine

# Replace the default "It works!" page with ours.
COPY index.html /usr/local/apache2/htdocs/index.html

# httpd listens on 80 inside the container.
EXPOSE 80

# The base image already has:  CMD ["httpd-foreground"]
# httpd-foreground runs httpd in the FOREGROUND. A container exits the moment
# PID 1 exits, so a daemonised web server would kill the container instantly.
