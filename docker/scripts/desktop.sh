#!/usr/bin/env bash
# Legacy XFCE/Xvfb helper retained from the local files. Neither platform's
# Dockerfile uses this: Mac inherits Tiryoh; Linux uses the host X11 display.
set -eo pipefail
source /opt/asv/environment.sh

export XDG_RUNTIME_DIR
XDG_RUNTIME_DIR="$(mktemp -d)"
touch "$XAUTHORITY"
xauth add "$DISPLAY" . "$(mcookie)"

pids=()
cleanup() {
  if (( ${#pids[@]} )); then
    kill "${pids[@]}" 2>/dev/null || true
    wait "${pids[@]}" 2>/dev/null || true
  fi
  rm -rf "$XDG_RUNTIME_DIR"
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT

Xvfb "$DISPLAY" -screen 0 "${ASV_SCREEN:-1280x800x24}" -nolisten tcp -auth "$XAUTHORITY" &
pids+=("$!")
for attempt in {1..50}; do
  if xdpyinfo >/dev/null 2>&1; then
    break
  fi
  sleep 0.2
done
xdpyinfo >/dev/null

dbus-run-session -- xfce4-session &
pids+=("$!")
x11vnc -display "$DISPLAY" -auth "$XAUTHORITY" -localhost -rfbport 5900 -forever -shared -nopw &
pids+=("$!")
websockify --web=/usr/share/novnc 0.0.0.0:6080 127.0.0.1:5900 &
pids+=("$!")

wait -n "${pids[@]}"
