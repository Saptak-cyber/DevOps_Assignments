#!/bin/bash
#===============================================================================
# Task 1 — Docker Container Networking
#
#   3 containers : frontend (nginx), backend (alpine), database (mysql)
#   3 networks   : frontend-net, backend-net, database-net
#   backend joins TWO networks, making it the only container that can reach
#   both the frontend and the database — the classic 3-tier isolation model.
#
#       frontend  ──frontend-net──  backend  ──database-net──  database
#                                      │
#                                  backend-net (spare/third network)
#
# Usage:  ./setup.sh          create everything and test connectivity
#         ./setup.sh clean    remove containers and networks
#===============================================================================

CONTAINERS="frontend backend database"
NETWORKS="frontend-net backend-net database-net"

clean() {
    echo "Removing containers and networks..."
    for c in $CONTAINERS; do docker rm -f "$c" >/dev/null 2>&1; done
    for n in $NETWORKS;  do docker network rm "$n" >/dev/null 2>&1; done
    echo "Done."
}

[ "${1:-}" = "clean" ] && { clean; exit 0; }

clean

echo "==============================================================="
echo " 1. Create three user-defined bridge networks"
echo "==============================================================="
# A user-defined bridge (unlike the default 'bridge') provides automatic
# DNS resolution between containers by NAME. That is the whole reason to
# create one instead of using the default network.
for n in $NETWORKS; do
    echo "\$ docker network create $n"
    docker network create "$n"
done

echo
echo "\$ docker network ls"
docker network ls

echo
echo "==============================================================="
echo " 2. Create the containers"
echo "==============================================================="

echo "\$ docker run -d --name frontend --network frontend-net nginx:alpine"
docker run -d --name frontend --network frontend-net nginx:alpine

echo "\$ docker run -d --name backend  --network frontend-net alpine sleep 3600"
docker run -d --name backend --network frontend-net alpine sleep 3600

echo "\$ docker run -d --name database --network database-net -e MYSQL_ROOT_PASSWORD=rootpass -e MYSQL_DATABASE=appdb mysql:8"
docker run -d --name database --network database-net \
    -e MYSQL_ROOT_PASSWORD=rootpass \
    -e MYSQL_DATABASE=appdb \
    mysql:8

echo
echo "==============================================================="
echo " 3. Connect backend to a SECOND network"
echo "==============================================================="
echo "\$ docker network connect database-net backend"
docker network connect database-net backend

echo
echo "Backend is now on: frontend-net AND database-net"
echo "\$ docker inspect backend --format '{{range \$k,\$v := .NetworkSettings.Networks}}{{\$k}}={{\$v.IPAddress}} {{end}}'"
docker inspect backend --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}={{$v.IPAddress}} {{end}}'
echo

echo "==============================================================="
echo " 4. Install ping inside the backend container"
echo "==============================================================="
docker exec backend sh -c 'apk add --no-cache iputils-ping bind-tools mysql-client >/dev/null 2>&1; echo installed'

echo
echo "==============================================================="
echo " 5. CONNECTIVITY TESTS"
echo "==============================================================="

echo
echo "--- backend -> frontend (SAME network: frontend-net) — EXPECT SUCCESS"
docker exec backend ping -c 2 frontend

echo
echo "--- backend -> database (SAME network: database-net) — EXPECT SUCCESS"
docker exec backend ping -c 2 database

echo
echo "--- frontend -> database (NO shared network) — EXPECT FAILURE"
docker exec frontend sh -c 'apk add --no-cache iputils-ping >/dev/null 2>&1; ping -c 2 database' \
    || echo ">>> FAILED AS EXPECTED: frontend and database share no network"

echo
echo "--- DNS resolution from backend"
docker exec backend nslookup frontend
docker exec backend nslookup database

echo
echo "--- backend -> database on the MySQL port (real service check)"
docker exec backend sh -c 'nc -zv database 3306' \
    || echo "(MySQL may still be initialising — retry in ~20 s)"

echo
echo "==============================================================="
echo " 6. Inspect the networks"
echo "==============================================================="
for n in $NETWORKS; do
    echo
    echo "--- $n containers:"
    docker network inspect "$n" \
      --format '{{range .Containers}}{{.Name}} ({{.IPv4Address}}){{println}}{{end}}'
done

echo
echo "Tear down with: ./setup.sh clean"
