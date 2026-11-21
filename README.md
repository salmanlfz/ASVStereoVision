# ASV Simulator

Satu repo, satu branch utama `main`, dan kode ROS bersama di `asv_ws/src`.
Stack: Ubuntu 22.04, ROS 2 Humble, Gazebo **Garden (gz-sim 7)**,
bridge `ros-humble-ros-gzgarden-*`, serta [fork VRX](https://github.com/salmanlfz/vrx)

## Pilih platform

| Host | Tampilan simulator | Panduan lengkap |
| --- | --- | --- |
| Mac Apple Silicon + OrbStack | Desktop MATE melalui noVNC di browser | [Setup macOS](docs/setup-macos.md) |
| Linux x86-64 dengan sesi X11 lokal | Jendela Gazebo di desktop host | [Setup Linux](docs/setup-linux.md) |

Siapkan Docker CLI, Docker Compose v2, dan koneksi internet untuk mengunduh
image, paket, serta model Fuel. Mac menjalankan image `linux/amd64` melalui
emulasi OrbStack. Linux memerlukan Bash, `xauth`, `mesa-utils`, dan akses Docker
untuk user aktif.

Semua perintah **terminal host** dijalankan dari root repo. Perintah
**terminal container** dijalankan setelah masuk ke container atau membuka
terminal MATE di browser.

## Mulai di macOS

Pastikan OrbStack aktif, lalu jalankan di **Terminal Mac**:

```bash
docker context use orbstack
docker compose version
docker compose -f docker/mac/compose.yaml build
docker compose -f docker/mac/compose.yaml up -d --wait --wait-timeout 120
open http://127.0.0.1:6080/vnc.html
```

Klik **Connect** di noVNC, lalu buka terminal MATE untuk menjalankan arena.
Untuk masuk melalui **Terminal Mac**, gunakan:

```bash
docker compose -f docker/mac/compose.yaml exec --user ubuntu asv dbus-run-session -- bash
```

Pada penggunaan berikutnya, cukup jalankan perintah `up`, buka alamat noVNC,
lalu jalankan arena. Jika port 6080 dipakai, gunakan `ASV_PORT=6081` pada setiap
perintah Compose dan buka `http://127.0.0.1:6081/vnc.html`.

## Mulai di Linux

Gunakan **Bash pada terminal desktop host** dengan sesi X11 lokal:

```bash
uname -m                         # harus x86_64
printf 'session=%s DISPLAY=%s\n' "$XDG_SESSION_TYPE" "$DISPLAY"
glxinfo -B
source docker/scripts/linux-x11.sh
docker compose -f docker/linux/compose.yaml build
docker compose -f docker/linux/compose.yaml up -d
docker compose -f docker/linux/compose.yaml exec asv xdpyinfo >/dev/null
docker compose -f docker/linux/compose.yaml exec asv glxinfo -B
docker compose -f docker/linux/compose.yaml exec asv dbus-run-session -- bash
```

Skrip `linux-x11.sh` menyiapkan cookie Xauthority serta UID/GID host.
Jalankan `source` kembali di setiap terminal host baru sebelum memakai Compose,
dan setelah login ulang. Konfigurasi dasar memakai software rendering Mesa.
Opsi GPU Intel/AMD dan NVIDIA tersedia di [panduan Linux](docs/setup-linux.md).

## Jalankan arena

Di **terminal container pertama**:

```bash
source /opt/asv/environment.sh
ros2 launch vrx_gz arena.launch.py arena:=1
```

| Arena | Kegunaan |
| --- | --- |
| `1` | Teleoperasi kapal |
| `2` | Kalibrasi stereo |
| `3` | Lintasan lurus |
| `4` | Lintasan zigzag |

Jalankan satu arena setiap waktu. Tekan `Ctrl+C` sebelum mengganti nilai `arena`.
Gazebo tampil di desktop noVNC pada Mac atau desktop host pada Linux.

## Build workspace dan jalankan teleop

Buka **terminal container kedua** dengan cara yang sama seperti di atas:

```bash
cd /workspace/asv_ws
colcon build --merge-install
source /opt/asv/environment.sh
python3 src/asv_stereo/asv_stereo/teleop.py
```

Fokuskan keyboard pada terminal teleop. Gunakan tombol panah untuk maju,
mundur, dan berbelok. Tanpa input, thrust kembali ke nol. Tekan `Ctrl+C`
untuk keluar. Script dijalankan langsung karena `setup.py` belum
mendaftarkan console script.

Edit kode di `asv_ws/src` dari host. Direktori ini di-bind mount ke
`/workspace/asv_ws/src` dalam container. Setelah perubahan, build ulang jika
diperlukan dan source kembali `/opt/asv/environment.sh`.

## Periksa kamera stereo

Saat arena berjalan, buka **terminal container lain**:

```bash
/opt/asv/check-stereo.sh
source /opt/asv/environment.sh
ros2 topic hz /wamv/sensors/cameras/front_left_camera_sensor/image_raw
```

Helper stereo memeriksa pesan dari kedua kamera beserta `camera_info`.
Gunakan arena 2 untuk praktikum kalibrasi stereo.

## Log, stop, dan restart

Jalankan di **terminal host**. Contoh memakai Mac; untuk Linux, ganti
`docker/mac/compose.yaml` dengan `docker/linux/compose.yaml` setelah menyiapkan
Xauthority. Pilih perintah sesuai kebutuhan:

```bash
docker compose -f docker/mac/compose.yaml logs -f
docker compose -f docker/mac/compose.yaml stop
docker compose -f docker/mac/compose.yaml start
docker compose -f docker/mac/compose.yaml restart
docker compose -f docker/mac/compose.yaml down
```

Setelah container dijalankan ulang, luncurkan arena lagi. `down` menghapus
container beserta hasil build Colcon di dalamnya; source di host tetap
tersimpan. Build ulang workspace setelah membuat container baru.

## Struktur repo

```text
asv_ws/src/asv_stereo/  # paket ROS: teleop, visi stereo, dan kendali otonom
docker/
  mac/                 # Dockerfile dan Compose untuk OrbStack/noVNC
  linux/               # Dockerfile, Compose X11, dan overlay GPU
  scripts/             # instalasi, build VRX, environment, dan diagnostik
docs/                  # panduan platform dan catatan verifikasi
```

Compose utama sudah memuat konfigurasi build.
`docker/mac/compose.build.yaml` tersedia sebagai override kompatibilitas.
Kedua platform memakai image dan project Compose yang berbeda.

## Troubleshooting

- **Docker tidak tersambung pada Mac:** pastikan OrbStack aktif, lalu cek
  `docker context ls` dan `docker info`.
- **noVNC gagal tersambung:** jalankan
  `python3 docker/scripts/diagnose-vnc.py` dari host. Status healthy belum
  membuktikan koneksi desktop browser berhasil.
- **GUI gagal muncul melalui CLI:** masuk menggunakan
  `dbus-run-session -- bash` seperti contoh platform di atas.
- **Linux gagal membuka display:** pastikan sesi X11 aktif dan source ulang
  `docker/scripts/linux-x11.sh` dari terminal desktop host.
- **Gazebo lambat:** Mac menggunakan emulasi amd64, sedangkan konfigurasi Linux
  dasar memakai software rendering. Periksa `glxinfo -B` dalam container;
  inisialisasi viewport pertama dapat memerlukan waktu.
- **Unduhan Fuel gagal saat build:** tambahkan `PREFETCH_FUEL=0` sebelum perintah
  Compose `build`. Model kemudian perlu diunduh saat arena diluncurkan.
- **Error NumPy/cv_bridge:** jalankan
  `python3 /opt/asv/check-vision-python.py` dalam terminal container setelah
  source environment ROS.

Lihat panduan platform untuk diagnostik lanjutan dan cara berbagi image.

## Stack dan status verifikasi

Stack memakai bridge Garden khusus `ros-humble-ros-gzgarden-*`.
Digest base Tiryoh dipatok; base Linux default adalah
`ros:humble-ros-base-jammy` dan dapat diganti melalui `ROS_BASE`.
Paket APT dan aset Fuel tetap bergantung pada repositori saat build.

Build dan smoke test Mac telah dicatat, termasuk desktop noVNC, arena 1,
pesan kamera, dan thrust teleop. Gerak kapal akibat input serta performa kamera
belum diukur. Konfigurasi Linux telah divalidasi, tetapi build penuh konfigurasi
terakhir, runtime X11, dan GPU pada desktop Linux nyata masih perlu diuji.
Wayland/XWayland dan SSH X11 forwarding juga belum diuji.
Lihat [catatan verifikasi](docs/verification.md) untuk bukti dan batas pengujian.
