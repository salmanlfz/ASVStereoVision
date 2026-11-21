#!/usr/bin/env bash
# Source in this order so participant packages can use the installed simulator.
source /opt/ros/humble/setup.bash
source /opt/vrx_ws/install/local_setup.bash
if [[ -f /workspace/asv_ws/install/local_setup.bash ]]; then
  source /workspace/asv_ws/install/local_setup.bash
fi
