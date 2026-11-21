#!/usr/bin/env bash
set -euo pipefail
# Remove inherited Gazebo Classic and Fortress bridge packages before Garden.
set -e; \
    test "$(dpkg --print-architecture)" = amd64; \
    dpkg-query -W -f='${db:Status-Status} ${Package}\n' | \
      awk '$1 == "installed" && $2 ~ /^(gazebo($|[-0-9])|libgazebo|ros-humble-(gazebo-|ros-ign($|-)|ros-gz($|-)))/ {print $2}' \
      > /tmp/asv-replaced-packages; \
    if [[ -s /tmp/asv-replaced-packages ]]; then \
      xargs -r env DEBIAN_FRONTEND=noninteractive apt-get purge -y < /tmp/asv-replaced-packages; \
    fi; \
    rm /tmp/asv-replaced-packages

apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl git && \
    curl --fail --silent --show-error --location --retry 3 \
      https://packages.osrfoundation.org/gazebo.gpg \
      -o /usr/share/keyrings/gazebo-osrf.gpg && \
    echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/gazebo-osrf.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable jammy main' \
      > /etc/apt/sources.list.d/gazebo-osrf.list && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      gz-garden libgz-rendering7-ogre2 python3-sdformat13 \
      ros-humble-ros-gzgarden-bridge ros-humble-ros-gzgarden-sim \
      ros-humble-ros-gzgarden-interfaces \
      ros-humble-ament-cmake ros-humble-ament-cmake-python \
      ros-humble-cv-bridge ros-humble-image-tools ros-humble-xacro \
      ros-humble-robot-state-publisher \
      build-essential libeigen3-dev patchelf python3-colcon-common-extensions \
      python3-opencv python3-yaml \
      libgl1-mesa-dri libglx-mesa0 mesa-utils && \
    rm -rf /var/lib/apt/lists/*

