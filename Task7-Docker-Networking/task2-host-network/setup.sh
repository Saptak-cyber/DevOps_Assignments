#!/bin/bash
#===============================================================================
# Task 2 — Host Network
#
# Pull the Apache2 (httpd) image and run it with --network host, then access it
# on port 80 with NO -p port mapping.
#
# IMPORTANT: --network host works natively only on LINUX. On macOS and Windows,
# Docker runs inside a small Linux VM, so "the host" is that VM, not your
# laptop. Docker Desktop 4.34+ added an opt-in host-networking feature
# (Settings -> Resources -> Network -> "Enable host networking"); without it,
# localhost:80 on the Mac will not reach the container.
#
# Usage:  ./setup.sh          run and test
#         ./setup.sh clean    remove the container
#===============================================================================

clean() { docker rm -f apache-host >/dev/null 2>&1; echo "Removed apache-host."; }
[ "${1:-}" = "clean" ] && { clean; exit 0; }
clean

echo "==============================================================="
echo " 1. Pull the Apache2 image from Docker Hub"
echo "==============================================================="
echo "\$ docker pull httpd:2.4"
docker pull httpd:2.4

echo
echo "==============================================================="
echo " 2. Run Apache with the HOST network"
echo "==============================================================="
echo "\$ docker run -d --name apache-host --network host httpd:2.4"
echo "   Note: NO -p flag. With --network host there is nothing to map --"
echo "   the container shares the host's network stack directly."
docker run -d --name apache-host --network host httpd:2.4

sleep 3

echo
echo "==============================================================="
echo " 3. Verify"
echo "==============================================================="
echo "\$ docker ps"
docker ps --filter name=apache-host --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
echo
echo "   The PORTS column is EMPTY -- that is the signature of host networking."
echo "   There is no NAT rule because there is no separate network namespace."

echo
echo "\$ docker inspect apache-host --format '{{.HostConfig.NetworkMode}}'"
docker inspect apache-host --format '{{.HostConfig.NetworkMode}}'

echo
echo "\$ docker inspect apache-host --format '{{.NetworkSettings.IPAddress}}'"
echo "   (empty -- the container has no IP of its own; it uses the host's)"
docker inspect apache-host --format '{{.NetworkSettings.IPAddress}}'

echo
echo "==============================================================="
echo " 4. Access the Apache website on port 80"
echo "==============================================================="
echo "\$ curl http://localhost:80"
curl -s --max-time 5 http://localhost:80 || echo "(see the macOS/Windows note at the top of this script)"

echo
echo "\$ curl -I http://localhost:80"
curl -s -I --max-time 5 http://localhost:80

echo
echo "--- Proof from INSIDE the container that it shares the host's netns ---"
docker exec apache-host sh -c 'apt-get update -qq >/dev/null 2>&1; apt-get install -y -qq iproute2 curl >/dev/null 2>&1; echo "== hostname =="; hostname; echo "== ip -br a =="; ip -br a; echo "== curl localhost =="; curl -s -I localhost'

echo
echo "Tear down with: ./setup.sh clean"
