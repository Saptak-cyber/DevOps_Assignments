#!/bin/bash
#===============================================================================
# Task 3 — Bind Mount
#
#   1. A local folder ./html with index.html containing "Hello students"
#   2. Bind-mounted into an nginx container
#   3. Access the site, edit the file on the HOST, and see the change appear
#      with NO container restart.
#
# Usage:  ./setup.sh          run the whole demo
#         ./setup.sh clean    remove the container
#===============================================================================

HTML_DIR="$(cd "$(dirname "$0")" && pwd)/html"

clean() { docker rm -f nginx-bind >/dev/null 2>&1; echo "Removed nginx-bind."; }
[ "${1:-}" = "clean" ] && { clean; exit 0; }
clean

echo "==============================================================="
echo " 1. The local folder and index.html"
echo "==============================================================="
mkdir -p "$HTML_DIR"
cat > "$HTML_DIR/index.html" <<'HTML'
<!doctype html>
<html>
  <head>
    <title>Bind Mount Demo</title>
    <meta charset="utf-8">
  </head>
  <body style="font-family: system-ui, sans-serif; text-align: center; padding: 60px;">
    <h1>Hello students</h1>
  </body>
</html>
HTML

echo "\$ ls -l $HTML_DIR"
ls -l "$HTML_DIR"
echo
echo "\$ cat $HTML_DIR/index.html"
cat "$HTML_DIR/index.html"

echo
echo "==============================================================="
echo " 2. Bind mount the folder into an nginx container"
echo "==============================================================="
echo "\$ docker run -d --name nginx-bind -p 8090:80 \\"
echo "      -v $HTML_DIR:/usr/share/nginx/html:ro nginx:alpine"
echo
echo "   -v <HOST PATH>:<CONTAINER PATH>[:options]"
echo "   The host path MUST be absolute. A relative path, or a bare name,"
echo "   is interpreted as a NAMED VOLUME instead of a bind mount."
echo "   :ro makes the mount read-only inside the container -- correct for"
echo "   static content the app should never modify."
docker run -d --name nginx-bind -p 8090:80 -v "$HTML_DIR":/usr/share/nginx/html:ro nginx:alpine

sleep 2

echo
echo "==============================================================="
echo " 3. Access the site"
echo "==============================================================="
echo "\$ curl http://localhost:8090"
curl -s http://localhost:8090

echo
echo "\$ docker inspect nginx-bind --format '{{json .Mounts}}'"
docker inspect nginx-bind --format '{{json .Mounts}}'

echo
echo "==============================================================="
echo " 4. Modify index.html ON THE HOST -- no container restart"
echo "==============================================================="
cat > "$HTML_DIR/index.html" <<'HTML'
<!doctype html>
<html>
  <head>
    <title>Bind Mount Demo - UPDATED</title>
    <meta charset="utf-8">
  </head>
  <body style="font-family: system-ui, sans-serif; text-align: center; padding: 60px;">
    <h1>Hello students - this file was edited on the host!</h1>
    <p>The nginx container was never restarted.</p>
  </body>
</html>
HTML
echo "File edited on the host."

echo
echo "\$ curl http://localhost:8090        # immediately, no restart"
curl -s http://localhost:8090

echo
echo "\$ docker ps    # confirm STATUS -- uptime proves it was never restarted"
docker ps --filter name=nginx-bind --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo
echo "--- Same file seen from inside the container ---"
echo "\$ docker exec nginx-bind cat /usr/share/nginx/html/index.html"
docker exec nginx-bind cat /usr/share/nginx/html/index.html

echo
echo "--- Read-only mount proof: writing from inside must FAIL ---"
echo "\$ docker exec nginx-bind sh -c 'echo hack > /usr/share/nginx/html/index.html'"
docker exec nginx-bind sh -c 'echo hack > /usr/share/nginx/html/index.html' \
    || echo ">>> BLOCKED AS EXPECTED: the mount is read-only (:ro)"

echo
echo "Tear down with: ./setup.sh clean"
