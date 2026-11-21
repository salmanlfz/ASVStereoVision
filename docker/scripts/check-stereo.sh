#!/usr/bin/env bash
set -eo pipefail
source /opt/asv/environment.sh

prefix=/wamv/sensors/cameras
topics=(
  "$prefix/front_left_camera_sensor/image_raw"
  "$prefix/front_right_camera_sensor/image_raw"
  "$prefix/front_left_camera_sensor/camera_info"
  "$prefix/front_right_camera_sensor/camera_info"
)
for topic in "${topics[@]}"; do
  printf '\n%s\n' "$topic"
  timeout 45s ros2 topic echo "$topic" --once --field header --qos-reliability best_effort
done
