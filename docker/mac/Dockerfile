# syntax=docker/dockerfile:1
ARG TIRYOH_BASE=tiryoh/ros2-desktop-vnc:humble@sha256:84127c508789237a03a3c3ec4fec2a2b5e7caa40c0ad57183cb60e6d1642c2aa
FROM ${TIRYOH_BASE}
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG VRX_COMMIT=8087723140143654c12a91ca1b756198f0f83f5c
ARG PREFETCH_FUEL=1
LABEL org.opencontainers.image.title="ASV Humble Garden (Mac desktop)" \
      dev.asv.vrx.revision="${VRX_COMMIT}"
COPY docker/scripts/install-garden.sh /opt/asv/install-garden.sh
RUN bash /opt/asv/install-garden.sh
COPY docker/scripts/environment.sh docker/scripts/prefetch-fuel.sh docker/scripts/check-stereo.sh docker/scripts/build-vrx.sh /opt/asv/
# Tiryoh creates ubuntu at runtime; keep its MATE/TigerVNC/noVNC startup.
RUN chmod 755 /opt/asv/*.sh && \
    ! getent passwd 1000 && \
    install -d -m 755 -o 1000 -g 1000 /opt/vrx_ws /workspace/asv_ws /workspace/asv_ws/src && \
    printf '\nsource /opt/asv/environment.sh\n' >> /etc/skel/.bashrc
RUN bash /opt/asv/build-vrx.sh
COPY docker/scripts/install-vision.sh docker/scripts/check-vision-python.py /opt/asv/
RUN bash /opt/asv/install-vision.sh
WORKDIR /workspace/asv_ws
EXPOSE 80
# Deliberately inherit Tiryoh's original entrypoint and command.
