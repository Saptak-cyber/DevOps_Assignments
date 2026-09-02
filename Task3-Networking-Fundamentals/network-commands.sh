#!/bin/bash
#===============================================================================
# network-commands.sh — runs every networking command from the homework and
# saves the combined output to network-output.txt so it can be pasted into the
# .md file (or screenshotted).
#
# Usage:  ./network-commands.sh            # run on the local machine
#         ./network-commands.sh docker     # run inside an Ubuntu container
#===============================================================================

OUT="network-output.txt"

run() {
    echo ""
    echo "==============================================================="
    echo "\$ $*"
    echo "==============================================================="
    eval "$@" 2>&1
}

if [ "${1:-}" = "docker" ]; then
    echo "Running the whole suite inside ubuntu:22.04 ..."
    docker run --rm -v "$PWD":/work ubuntu:22.04 bash -c '
        apt-get update -qq >/dev/null 2>&1
        apt-get install -y -qq iproute2 iputils-ping dnsutils curl net-tools \
                              traceroute nginx >/dev/null 2>&1
        service nginx start >/dev/null 2>&1
        bash /work/network-commands.sh' | tee "$OUT"
    exit 0
fi

{
echo "###############################################################"
echo "#  NETWORKING COMMAND OUTPUT — generated $(date)"
echo "#  Host: $(hostname)"
echo "###############################################################"

# --- 1. Interfaces and addresses -------------------------------------------
run "ip a"
run "ip link show"
run "ip -br a"
run "hostname -I"

# --- 2. Routing -------------------------------------------------------------
run "ip r"
run "ip route get 8.8.8.8"

# --- 3. Reachability --------------------------------------------------------
run "ping -c 4 8.8.8.8"
run "ping -c 4 google.com"

# --- 4. DNS -----------------------------------------------------------------
run "cat /etc/resolv.conf"
run "dig google.com +short"
run "dig google.com"
run "nslookup github.com"
run "host github.com"

# --- 5. Sockets / listening ports -------------------------------------------
run "ss -tulnp"
run "netstat -tulnp"
run "ss -s"

# --- 6. HTTP ----------------------------------------------------------------
run "curl -s -I https://example.com"
run "curl -s -o /dev/null -w 'code=%{http_code} time=%{time_total}s\n' https://example.com"

# --- 7. Path to a host ------------------------------------------------------
run "traceroute -m 8 8.8.8.8"

# --- 8. Local name resolution / ARP ------------------------------------------
run "cat /etc/hosts"
run "ip neigh"

} | tee "$OUT"

echo ""
echo "Saved to $OUT"
