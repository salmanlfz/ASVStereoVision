#!/usr/bin/env bash
# Source from a Bash terminal in the local Linux X11 desktop session.
_asv_x11_prepare() {
  if [[ "$(uname -s)" != Linux || "${XDG_SESSION_TYPE:-}" != x11 ]]; then
    echo 'Use a local Linux X11 session (XDG_SESSION_TYPE=x11). Wayland is untested.' >&2
    return 1
  fi
  if [[ ! "${DISPLAY:-}" =~ ^:[0-9]+(\.[0-9]+)?$ ]]; then
    echo 'Expected a local DISPLAY such as :0; SSH forwarding is not supported here.' >&2
    return 1
  fi
  command -v xauth >/dev/null || { echo 'Install xauth on the host first.' >&2; return 1; }
  local root records target
  root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)" || return
  records="$(xauth nlist "$DISPLAY")" || return
  if [[ -z "$records" ]]; then
    echo 'No Xauthority cookie for DISPLAY; check the host XAUTHORITY variable.' >&2
    return 1
  fi
  target="$root/.cache/asv/Xauthority"
  mkdir -p "$root/.cache/asv" || return
  # FamilyWild allows the cookie to match the container hostname.
  (umask 077; : > "$target"; printf '%s\n' "$records" | sed 's/^..../ffff/' | xauth -f "$target" nmerge -) || return
  chmod 600 "$target" || return
  export ASV_XAUTHORITY="$target" ASV_UID="$(id -u)" ASV_GID="$(id -g)"
  printf 'X11 ready: DISPLAY=%s, UID:GID=%s:%s, cookie=%s\n' "$DISPLAY" "$ASV_UID" "$ASV_GID" "$ASV_XAUTHORITY"
}
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo 'Run: source docker/scripts/linux-x11.sh' >&2
  exit 1
fi
_asv_x11_prepare
