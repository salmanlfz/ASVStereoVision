#!/usr/bin/env bash
set -eo pipefail
# Humble's binary cv_bridge and Jammy OpenCV use the NumPy 1.x ABI.
# Keep this after the VRX build so the compatibility fix can reuse that layer.
apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3-pip && \
    python3 -m pip install --no-cache-dir 'numpy==1.26.4' && \
    source /opt/ros/humble/setup.bash && \
    python3 /opt/asv/check-vision-python.py && \
    rm -rf /var/lib/apt/lists/*

