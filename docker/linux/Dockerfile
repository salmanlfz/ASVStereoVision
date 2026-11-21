# syntax=docker/dockerfile:1
ARG ROS_BASE=ros:humble-ros-base-jammy
FROM ${ROS_BASE}
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG VRX_COMMIT=8087723140143654c12a91ca1b756198f0f83f5c
ARG PREFETCH_FUEL=1
ARG ASV_UID=1000
ARG ASV_GID=1000
LABEL org.opencontainers.image.title="ASV Humble Garden (Linux X11)" \
      dev.asv.vrx.revision="${VRX_COMMIT}"
COPY docker/scripts/install-garden.sh /opt/asv/install-garden.sh
RUN bash /opt/asv/install-garden.sh && \
    apt-get update && apt-get install -y --no-install-recommends xauth x11-utils && \
    rm -rf /var/lib/apt/lists/*
RUN if ! getent group "${ASV_GID}" >/dev/null; then groupadd --gid "${ASV_GID}" ubuntu; fi && \
    useradd --uid "${ASV_UID}" --gid "${ASV_GID}" --create-home --shell /bin/bash ubuntu && \
    install -d -o "${ASV_UID}" -g "${ASV_GID}" /opt/vrx_ws /workspace/asv_ws /workspace/asv_ws/src
COPY docker/scripts/environment.sh docker/scripts/prefetch-fuel.sh docker/scripts/check-stereo.sh docker/scripts/build-vrx.sh docker/scripts/linux-entrypoint.sh /opt/asv/
RUN chmod 755 /opt/asv/*.sh && \
    printf '\nsource /opt/asv/environment.sh\n' >> /home/ubuntu/.bashrc
RUN FUEL_HOME=/home/ubuntu bash /opt/asv/build-vrx.sh && chown -R "${ASV_UID}:${ASV_GID}" /home/ubuntu
COPY docker/scripts/install-vision.sh docker/scripts/check-vision-python.py /opt/asv/
RUN bash /opt/asv/install-vision.sh
USER ubuntu
ENV HOME=/home/ubuntu
WORKDIR /workspace/asv_ws
ENTRYPOINT ["/opt/asv/linux-entrypoint.sh"]
CMD ["sleep", "infinity"]
