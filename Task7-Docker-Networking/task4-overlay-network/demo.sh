#!/bin/bash
#===============================================================================
# Task 4 — Overlay Network
#
# An overlay network needs SWARM MODE. This script initialises a single-node
# swarm, creates an overlay network, deploys two services on it, and shows the
# cross-service DNS and VIP load balancing that overlay provides.
#
# A single node cannot demonstrate the multi-HOST part -- see README.md for the
# two-node walkthrough. What it CAN show is everything else: the network driver,
# the VXLAN encapsulation, the ingress network, and service discovery.
#
# Usage:  ./demo.sh          run the demo
#         ./demo.sh clean    remove services, network, and leave the swarm
#===============================================================================

clean() {
    docker service rm web api >/dev/null 2>&1
    sleep 2
    docker network rm app-overlay >/dev/null 2>&1
    docker swarm leave --force >/dev/null 2>&1
    echo "Cleaned up: services removed, overlay network removed, swarm left."
}

[ "${1:-}" = "clean" ] && { clean; exit 0; }

echo "==============================================================="
echo " 1. Overlay networks require swarm mode"
echo "==============================================================="
echo "\$ docker network create -d overlay will-fail    # outside swarm mode"
docker network create -d overlay will-fail 2>&1 | head -2

echo
echo "\$ docker swarm init"
docker swarm init 2>&1 | head -8

echo
echo "==============================================================="
echo " 2. Swarm mode creates networks automatically"
echo "==============================================================="
echo "\$ docker network ls"
docker network ls

echo
echo "   Two new networks appeared:"
echo "     ingress            (overlay, swarm)  -- routing mesh for published ports"
echo "     docker_gwbridge    (bridge, local)   -- gives overlay containers"
echo "                                             outbound access to the internet"

echo
echo "==============================================================="
echo " 3. Create a user-defined overlay network"
echo "==============================================================="
echo "\$ docker network create --driver overlay --attachable app-overlay"
docker network create --driver overlay --attachable app-overlay
echo
echo "   --attachable lets standalone 'docker run' containers join it too."
echo "   Without it, ONLY swarm services can attach."

echo
echo "\$ docker network inspect app-overlay --format '{{.Name}} driver={{.Driver}} scope={{.Scope}} attachable={{.Attachable}} subnet={{range .IPAM.Config}}{{.Subnet}}{{end}}'"
docker network inspect app-overlay --format '{{.Name}} driver={{.Driver}} scope={{.Scope}} attachable={{.Attachable}} subnet={{range .IPAM.Config}}{{.Subnet}}{{end}}'
echo
echo "   scope=swarm (not 'local') is the key difference from a bridge network."

echo
echo "==============================================================="
echo " 4. Deploy two services on the overlay"
echo "==============================================================="
echo "\$ docker service create --name web --network app-overlay --replicas 3 -p 8091:80 nginx:alpine"
docker service create --name web --network app-overlay --replicas 3 -p 8091:80 nginx:alpine

echo
echo "\$ docker service create --name api --network app-overlay --replicas 2 alpine sleep 3600"
docker service create --name api --network app-overlay --replicas 2 alpine sleep 3600

echo
echo "\$ docker service ls"
docker service ls

echo
echo "\$ docker service ps web"
docker service ps web

echo
echo "==============================================================="
echo " 5. Service discovery over the overlay"
echo "==============================================================="
TASK=$(docker ps --filter "name=api." --format "{{.Names}}" | head -1)
echo "Testing from container: $TASK"
echo
echo "--- 'web' resolves to a VIP (virtual IP), not a container IP ---"
docker exec "$TASK" nslookup web 2>&1 | tail -5
echo
echo "--- tasks.web resolves to EVERY replica's real IP ---"
docker exec "$TASK" nslookup tasks.web 2>&1 | tail -8
echo
echo "--- HTTP through the VIP: the swarm load-balances across the 3 replicas ---"
docker exec "$TASK" sh -c 'apk add --no-cache curl >/dev/null 2>&1; for i in 1 2 3; do curl -s -o /dev/null -w "request $i -> HTTP %{http_code}\n" http://web; done'

echo
echo "==============================================================="
echo " 6. The published port goes through the ROUTING MESH"
echo "==============================================================="
echo "\$ curl -I http://localhost:8091"
curl -s -I --max-time 5 http://localhost:8091 | head -3
echo
echo "   In a multi-node swarm, port 8091 answers on EVERY node, even ones"
echo "   running no replica -- the ingress network forwards the request to a"
echo "   node that has one. That is the routing mesh."

echo
echo "Tear down with: ./demo.sh clean"
