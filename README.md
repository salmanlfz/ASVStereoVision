# ASV Simulator

Satu repo, satu branch utama `main`, dan kode ROS bersama di `asv_ws/src`.
Stack: Ubuntu 22.04, ROS 2 Humble, Gazebo **Garden (gz-sim 7)**,
bridge `ros-humble-ros-gzgarden-*`, serta [fork VRX](https://github.com/salmanlfz/vrx)
commit `8087723140143654c12a91ca1b756198f0f83f5c`.

- **Mac Apple Silicon + OrbStack:** [setup macOS](docs/setup-macos.md), desktop MATE/TigerVNC/noVNC melalui `127.0.0.1:6080`.
- **Linux x86-64:** [setup Linux](docs/setup-linux.md), jendela Gazebo di desktop X11 host dengan Xauthority. Software rendering default; GPU opsional.
- [Hasil verifikasi lokal dan batas pengujian](docs/verification.md).

Semua perintah panduan dijalankan dari root repo. Jalur lama `compose.yaml`,
`Dockerfile`, dan `scripts/` sekarang berada di `docker/mac/` dan `docker/scripts/`.
`docker/mac/compose.build.yaml` dipertahankan sebagai override kompatibilitas,
tetapi Compose Mac utama sudah memuat konfigurasi build.

```text
asv_ws/src/             # kode praktikum yang dipakai kedua platform
docker/
  mac/                 # Tiryoh amd64 melalui emulasi OrbStack
  linux/               # ROS Humble Jammy amd64, X11 host
  scripts/             # instalasi Garden, build VRX, environment, diagnostik
docs/                 # panduan platform dan bukti verifikasi
```

Image platform memakai tag dan project Compose berbeda. Tidak perlu branch khusus
platform: pengembangan dilakukan di branch fitur lalu direview untuk `main`.
Repo lokal saat pengerjaan belum memiliki commit pertama; perubahan ini dibiarkan
pada `feat/linux-docker` tanpa commit, merge, atau push.

Garden dipertahankan untuk kesesuaian stack lokal. Paket APT/aset Fuel tetap
bergantung pada repositori saat build; commit VRX dan digest base Tiryoh dipatok.
Base Linux default `ros:humble-ros-base-jammy` dapat diganti dengan digest melalui
`ROS_BASE`. Bagikan image dengan `docker image save` atau digest registry bila
membutuhkan byte image yang sama. [Dokumentasi Garden](https://gazebosim.org/docs/garden/install_ubuntu/)
dan [GPU Compose](https://docs.docker.com/compose/how-tos/gpu-support/).
