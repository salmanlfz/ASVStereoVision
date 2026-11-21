# Mac Apple Silicon / OrbStack

## Prasyarat

OrbStack aktif, Docker CLI + Compose v2, browser, dan koneksi internet untuk
paket serta aset Fuel. Image ini **linux/amd64**, dijalankan dengan emulasi pada
Apple Silicon; performa simulasi bergantung pada alokasi CPU/RAM OrbStack.
Desktop mengikuti entrypoint asli Tiryoh: MATE, TigerVNC, noVNC. Tidak ada
penggantian entrypoint dengan skrip desktop lama.

## Build dan start (Terminal Mac, root repo)

```bash
docker context use orbstack
docker compose version
docker compose -f docker/mac/compose.yaml config
docker compose -f docker/mac/compose.yaml build
docker compose -f docker/mac/compose.yaml up -d --wait --wait-timeout 120
open http://127.0.0.1:6080/vnc.html
```

Klik **Connect** di noVNC. Port hanya dipublikasikan pada loopback Mac.
Pada penggunaan berikutnya cukup `up -d --wait`, lalu buka URL yang sama.
Variabel `ASV_PORT=6081` dapat diberikan pada perintah Compose bila 6080 dipakai.
Gunakan nilai yang sama pada perintah berikutnya.

## Arena dan teleop

Di terminal **MATE dalam browser**, jalankan:

```bash
source /opt/asv/environment.sh
ros2 launch vrx_gz arena.launch.py arena:=1
```

Arena 1: teleoperasi; 2: kalibrasi stereo; 3: lintasan lurus; 4: zigzag.
Jalankan satu arena setiap waktu; Ctrl+C sebelum berganti arena.
Buka terminal MATE kedua untuk kode lokal:

```bash
cd /workspace/asv_ws
colcon build --merge-install
source /opt/asv/environment.sh
python3 src/asv_stereo/asv_stereo/teleop.py
```

Tombol panah mengendalikan thrust; Ctrl+C berhenti. `setup.py` lokal belum
mendaftarkan console script, jadi teleop dijalankan langsung tanpa mengubah
kode praktikum. Alternatif dari Terminal Mac:

```bash
docker compose -f docker/mac/compose.yaml exec --user ubuntu asv dbus-run-session -- bash
# Di shell container: jalankan perintah arena atau teleop di atas.
```

Pada arena 2, di terminal container lain:

```bash
/opt/asv/check-stereo.sh
ros2 topic hz /wamv/sensors/cameras/front_left_camera_sensor/image_raw
```

Edit `asv_ws/src` dari Mac; direktori ini di-bind mount ke workspace container.
Build peserta tersimpan di container. `down` menghapus hasil build tersebut,
namun kode lokal tetap tersedia; build ulang dengan Colcon setelah membuat
container baru.

## Stop, restart, log

Dari root repo di Terminal Mac:

```bash
docker compose -f docker/mac/compose.yaml logs -f
docker compose -f docker/mac/compose.yaml stop
docker compose -f docker/mac/compose.yaml start
docker compose -f docker/mac/compose.yaml restart
docker compose -f docker/mac/compose.yaml down
```

Pilih perintah sesuai kebutuhan; setelah restart, jalankan arena lagi.

## Troubleshooting

- Docker tidak tersambung: buka OrbStack, periksa `docker context ls` dan `docker info`.
- noVNC gagal Connect: `python3 docker/scripts/diagnose-vnc.py` mengecek HTTP,
  WebSocket, dan protokol RFB dari host. Healthcheck Compose hanya mengecek HTTP
  dan listener VNC, bukan bukti desktop browser tersambung. Hindari probe TCP/RFB
  tanpa autentikasi berulang yang bisa memicu blacklist TigerVNC.
- GUI macet saat diluncurkan lewat `exec`: gunakan shell `dbus-run-session -- bash`
  seperti contoh di atas, atau terminal MATE yang sudah memiliki sesi D-Bus.
- Gazebo lambat/gagal render: jalankan `glxinfo -B` dan
  `gz sim -v 4 -r shapes.sdf` di terminal MATE. Periksa renderer yang benar-benar
  terpilih; jalur Mac tidak menjanjikan GPU passthrough. Pada emulasi,
  jendela/viewport pertama dapat lambat muncul; periksa log dan tunggu inisialisasi
  Ogre2 sebelum menyimpulkan gagal render.
- Fuel gagal: `PREFETCH_FUEL=0 docker compose -f docker/mac/compose.yaml build`
  melewati prefetch; arena nanti memerlukan koneksi Fuel saat peluncuran.
- Jangan mengganti bridge dengan `ros-humble-ros-gz` generik; stack ini memakai
  paket Garden khusus `ros-humble-ros-gzgarden-*`.
- NumPy/cv_bridge: image mempertahankan pin NumPy 1.26.4 dan tes konversi gambar
  lokal. Cek ulang dengan `python3 /opt/asv/check-vision-python.py` dalam shell ROS.

## Berbagi image

```bash
docker image save asv-humble-garden:0.2.0 | gzip > asv-humble-garden-amd64.tar.gz
# Komputer penerima, dari root salinan repo:
docker image load -i asv-humble-garden-amd64.tar.gz
docker compose -f docker/mac/compose.yaml up -d --no-build
```

Untuk registry: `ASV_IMAGE=ghcr.io/OWNER/REPO:sha-COMMIT-mac` pada setiap
perintah Compose, lalu `pull` dan `up -d --no-build`. Workflow manual dapat
menerbitkan image setelah tesnya lulus. Tag image Mac dan Linux berbeda.
