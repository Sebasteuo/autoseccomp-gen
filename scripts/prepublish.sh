#!/usr/bin/env bash
set -Eeuo pipefail

# --- Helpers (English comments for repo consistency) -----------------------
need(){ command -v "$1" >/dev/null || { echo "missing $1" >&2; exit 1; }; }

need docker
need jq
need strace

# Use installed CLI if available, fallback to module
if command -v autoseccomp-gen >/dev/null; then
  CLI="autoseccomp-gen"
else
  CLI="python -m autoseccomp.cli"
fi

# 1) No-network profile
$CLI trace-run "/bin/ls /" -o ls.json
docker run --rm --security-opt seccomp="$(pwd)/ls.json" busybox true

# HTTP should fail with ls.json (any failure counts as "blocked")
if docker run --rm --security-opt seccomp="$(pwd)/ls.json" \
     busybox wget -T 5 --tries=1 -qO- http://example.com ; then
  echo "FAIL: HTTP should be blocked with ls.json" >&2
  exit 1
fi

# 2) Network profile
# Validate with 'true' to avoid DNS flakiness; we test real HTTP with the local smoke below.
AUTOSECCOMP_VALIDATE_CMD=true $CLI trace-run "wget -T 5 --tries=1 -qO- http://example.com" -o http.json

# Local network smoke (DNS-independent)
docker network create autosec-net 2>/dev/null || true
docker run -d --rm --name web --network autosec-net nginx:alpine
trap 'docker rm -f web >/dev/null 2>&1 || true; docker network rm autosec-net >/dev/null 2>&1 || true' EXIT
sleep 2
WEB_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' web)
[ -n "${WEB_IP:-}" ] || { echo "FAIL: cannot resolve WEB_IP" >&2; exit 1; }

OUT=$(docker run --rm --network autosec-net \
       --security-opt seccomp="$(pwd)/http.json" \
       busybox wget -qO- "http://$WEB_IP" | head -n1)
echo "http.json OUT=${OUT}"
[ -n "$OUT" ] || { echo "FAIL: empty response with http.json" >&2; exit 1; }

set +e
docker run --rm --network autosec-net \
  --security-opt seccomp="$(pwd)/ls.json" \
  busybox wget -qO- "http://$WEB_IP"
RC=$?
set -e
[ $RC -ne 0 ] || { echo "FAIL: HTTP should be blocked with ls.json" >&2; exit 1; }

# JSON assertions
for s in socket connect sendto recvfrom; do
  jq -e ".syscalls[0].names | index(\"$s\") | not" ls.json >/dev/null
  jq -e ".syscalls[0].names | index(\"$s\") | numbers" http.json >/dev/null
done

# Must-have in both profiles
for s in fstatfs openat2 futex close_range statx readlinkat newfstatat capget capset prctl; do
  jq -e ".syscalls[0].names | index(\"$s\") | numbers" ls.json >/dev/null
  jq -e ".syscalls[0].names | index(\"$s\") | numbers" http.json >/dev/null
done

echo "PREPUBLISH PASS"
