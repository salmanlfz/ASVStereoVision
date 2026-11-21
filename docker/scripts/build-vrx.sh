#!/usr/bin/env bash
set -eo pipefail
    repo=/opt/vrx_ws/src/vrx; \
    git init -q "$repo"; \
    git -C "$repo" remote add origin https://github.com/salmanlfz/vrx.git; \
    git -C "$repo" fetch --depth 1 origin "${VRX_COMMIT}"; \
    git -C "$repo" checkout --detach FETCH_HEAD; \
    test "$(git -C "$repo" rev-parse HEAD)" = "${VRX_COMMIT}"; \
    source /opt/ros/humble/setup.bash; \
    cd /opt/vrx_ws; \
    MAKEFLAGS=-j2 colcon build --merge-install --executor sequential \
      --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF; \
    if [[ "${PREFETCH_FUEL}" = 1 ]]; then \
      HOME="${FUEL_HOME:-/etc/skel}" /opt/asv/prefetch-fuel.sh "$repo"; \
    fi; \
    rm -rf /opt/vrx_ws/build /opt/vrx_ws/log "$repo/.git"; \
    chown -R "${ASV_UID:-1000}:${ASV_GID:-1000}" /opt/vrx_ws

