#!/bin/bash
#===============================================================================
# build-and-run-all.sh — builds and runs all six Hello World applications,
# then verifies each one over HTTP.
#
# Usage:  ./build-and-run-all.sh          build, run and verify
#         ./build-and-run-all.sh clean    stop and remove everything
#===============================================================================

# folder | image name | container name | host port | container port
APPS=(
  "nodejs-app|nodejs-hello|node-hello|3000|3000"
  "python-app|python-hello|python-hello-c|5001|5000"
  "java-app|java-hello|java-hello-c|8081|8080"
  "apache-app|apache-hello|apache-hello-c|8082|80"
  "nginx-app|nginx-hello|nginx-hello-c|8083|80"
  "react-app|react-hello|react-hello-c|8084|80"
)

clean() {
  echo "Stopping and removing containers..."
  for entry in "${APPS[@]}"; do
    IFS='|' read -r dir image container hport cport <<< "$entry"
    docker rm -f "$container" >/dev/null 2>&1
  done
  echo "Done."
}

if [ "${1:-}" = "clean" ]; then clean; exit 0; fi

clean

echo "==============================================================="
echo " BUILDING IMAGES"
echo "==============================================================="
for entry in "${APPS[@]}"; do
  IFS='|' read -r dir image container hport cport <<< "$entry"
  echo ""
  echo "--> docker build -t $image ./$dir"
  docker build -t "$image" "./$dir" || exit 1
done

echo ""
echo "==============================================================="
echo " RUNNING CONTAINERS"
echo "==============================================================="
for entry in "${APPS[@]}"; do
  IFS='|' read -r dir image container hport cport <<< "$entry"
  echo "--> docker run -d --name $container -p $hport:$cport $image"
  docker run -d --name "$container" -p "$hport:$cport" "$image" >/dev/null || exit 1
done

echo ""
echo "Waiting for the applications to come up..."
sleep 5

echo ""
echo "==============================================================="
echo " docker ps"
echo "==============================================================="
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "==============================================================="
echo " VERIFYING EACH APPLICATION"
echo "==============================================================="
for entry in "${APPS[@]}"; do
  IFS='|' read -r dir image container hport cport <<< "$entry"
  echo ""
  echo "--- $dir  ->  http://localhost:$hport"
  curl -s "http://localhost:$hport" | grep -oE '<h1>[^<]*</h1>|<title>[^<]*</title>' | head -2
  curl -s -o /dev/null -w "    HTTP %{http_code}  size=%{size_download}B  time=%{time_total}s\n" \
       "http://localhost:$hport"
done

echo ""
echo "==============================================================="
echo " IMAGE SIZES"
echo "==============================================================="
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep -E "REPOSITORY|hello"

echo ""
echo "Open these in a browser:"
for entry in "${APPS[@]}"; do
  IFS='|' read -r dir image container hport cport <<< "$entry"
  echo "  $dir  ->  http://localhost:$hport"
done
echo ""
echo "Tear everything down with: ./build-and-run-all.sh clean"
