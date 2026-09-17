#!/usr/bin/env bash
# O2Jam Music Shop — start / stop / status the local song server.
#
#   shop-up.sh start     start the shop server (default 127.0.0.1:8099)
#   shop-up.sh stop      stop it
#   shop-up.sh status    is it up? how many songs?
#   shop-up.sh rebuild   re-scan the libraries and rebuild Patch/MUSIC
#
# The client must be launched with O2JAM_SHOP_URL=http://127.0.0.1:8099 (run-windowed.sh
# does this automatically) so the in-game MUSIC SHOP downloads from this server.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$HERE"
PORT="${SHOP_PORT:-8099}"
HOST="${SHOP_HOST:-127.0.0.1}"
LOG="$HOME/o2jam/shop/shop-server.log"
PID="$HOME/o2jam/shop/shop-server.pid"

case "${1:-status}" in
  start)
    if [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null; then
      echo "shop already running (pid $(cat "$PID")) on $HOST:$PORT"
      exit 0
    fi
    if [ ! -d "$ROOT/Patch/MUSIC" ]; then
      echo "no library yet - building it first"
      python3 "$HERE/build-shop-library.py" --root "$ROOT" || exit 1
    fi
    nohup python3 "$HERE/shop-server.py" --root "$ROOT" --host "$HOST" --port "$PORT" >"$LOG" 2>&1 &
    echo $! > "$PID"
    sleep 1
    if kill -0 "$(cat "$PID")" 2>/dev/null; then
      echo "shop started (pid $(cat "$PID")) on http://$HOST:$PORT"
      echo "log: $LOG"
    else
      echo "shop FAILED to start - see $LOG"; tail -5 "$LOG"; exit 1
    fi
    ;;
  stop)
    if [ -f "$PID" ]; then
      kill "$(cat "$PID")" 2>/dev/null && echo "shop stopped (pid $(cat "$PID"))" || echo "not running"
      rm -f "$PID"
    else
      pkill -f "shop-server.py --root $ROOT" 2>/dev/null && echo "shop stopped" || echo "not running"
    fi
    ;;
  status)
    if [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null; then
      n=$(ls "$ROOT/Patch/MUSIC" 2>/dev/null | grep -c '\.ojn$')
      echo "shop UP   pid $(cat "$PID")   http://$HOST:$PORT   $n songs   root $ROOT"
    else
      echo "shop DOWN ($HOST:$PORT)"
    fi
    ;;
  rebuild)
    python3 "$HERE/build-shop-library.py" --root "$ROOT"
    python3 "$HERE/build-playlist.py" --shop "$ROOT"
    ;;
  *)
    echo "usage: $0 {start|stop|status|rebuild}"; exit 2;;
esac
