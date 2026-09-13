#!/bin/zsh
# A second dashboard on this machine that holds no state of its own.
#
# The page, its CSS and the slide JPGs come off local disk; every /api call is
# forwarded to the host that owns the state. So there is still one sync, one
# scheduler and one delivery log, and drafting from here writes there.
#
#   tools/local-dashboard.sh            # start (or restart)
#   tools/local-dashboard.sh stop
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${ARCO_PORT:-4501}"
# Empty means this machine owns the data. Set it to point at another host.
HOST="${ARCO_UPSTREAM:-}"
PIDFILE="/tmp/arco-local-$PORT.pid"

# Env vars are not in a process's argv, so `pkill -f ARCO_PORT=4501` matches
# nothing and the old server keeps the port. A pid file is the only thing that
# reliably identifies this instance without also killing a real dashboard.
stop() {
  [ -f "$PIDFILE" ] && kill "$(cat "$PIDFILE")" 2>/dev/null || true
  rm -f "$PIDFILE"
  # Whatever still holds the port, ours or a stale copy.
  lsof -ti tcp:"$PORT" 2>/dev/null | xargs -r kill 2>/dev/null || true
  sleep 1
}

if [ "$1" = "stop" ]; then stop; echo "stopped"; exit 0; fi

KEY="${ARCO_UPSTREAM_KEY:-$(cat "$REPO/tools/.dashboard_token" 2>/dev/null)}"
[ -n "$KEY" ] || { echo "no upstream key: set ARCO_UPSTREAM_KEY"; exit 1; }

if [ -n "$HOST" ]; then
  curl -sf -o /dev/null --max-time 15 "$HOST/?k=$KEY" \
    || { echo "! $HOST is not answering"; exit 1; }
fi

stop
ARCO_PORT="$PORT" ${HOST:+ARCO_UPSTREAM="$HOST"} ${HOST:+ARCO_UPSTREAM_KEY="$KEY"} \
  nohup python3 "$REPO/tools/dashboard.py" > /tmp/arco-local.log 2>&1 &
echo $! > "$PIDFILE"
# Dating posts from git history takes a moment on a cold start.
sleep 8

if ! kill -0 "$(cat "$PIDFILE")" 2>/dev/null || ! curl -sf -o /dev/null "localhost:$PORT/"; then
  # It used to die on "address already in use" and still print success,
  # so the browser kept being served by the old process.
  echo "! did not start:"; tail -4 /tmp/arco-local.log; rm -f "$PIDFILE"; exit 1
fi
echo "running  http://localhost:$PORT   ${HOST:+(data from $HOST)}${HOST:-(this machine owns the data)}"
[ -n "$HOST" ] && echo "upstream $HOST"
echo "log    /tmp/arco-local.log"
