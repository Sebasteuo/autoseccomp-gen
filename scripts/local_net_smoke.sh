#!/usr/bin/env bash
set -Eeuo pipefail

# --- Helpers (in English) --------------------------------------------------
_die(){ echo "ERROR: $*" >&2; exit 1; }
_need(){ command -v "$1" >/dev/null || _die "missing $1"; }

_need docker
[ -f http.json ] || _die "http.json not found (run the tracer first)"
[ -f ls.json   ] || _die "ls.json not found  (run the tracer first)"

cleanup(){
  docker rm -f web >/dev/null 2>&1 || true
  docker network rm autosec-net >/dev/null 2>&1 || true
}
trap cleanup EXIT

# --- Network setup ---------------------------------------------------------
docker network create autosec-net 2>/dev/null || true
docker run -d --rm --name web --network autosec-net nginx:alpine
sleep 2
WEB_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' web)
[ -n "${WEB_IP:-}" ] || _die "cannot resolve WEB_IP"
echo "WEB_IP=${WEB_IP}"

# --- Positive: http.json must allow HTTP -----------------------------------
set +e
OUT=$(docker run --rm --network autosec-net \
  --security-opt seccomp="$(pwd)/http.json" \
  busybox wget -qO- "http://${WEB_IP}" | head -n1)
RC=$?
set -e
echo "http.json RC=${RC} OUT=${OUT}"
[ ${RC} -eq 0 ] || _die "http.json should have allowed HTTP"

# --- Negative: ls.json must block HTTP -------------------------------------
set +e
docker run --rm --network autosec-net \
  --security-opt seccomp="$(pwd)/ls.json" \
  busybox wget -qO- "http://${WEB_IP}"
RC=$?
set -e
echo "ls.json RC=${RC}"
[ ${RC} -ne 0 ] || _die "ls.json should have blocked HTTP"
echo "OK: network blocked with ls.json"

# --- Init sanity ------------------------------------------------------------
docker run --rm --security-opt seccomp="$(pwd)/ls.json" busybox true \
  || _die "container should start with ls.json"

echo "SMOKE PASS"
