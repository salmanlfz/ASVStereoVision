# Linux x86-64 / desktop X11

## Prasyarat

Desktop Linux x86-64 dengan sesi **X11 lokal**, Docker Engine, Compose v2,
akses Docker untuk user saat ini, Bash, `xauth`, dan `mesa-utils` pada host.
Pada Ubuntu host: `sudo apt-get install xauth mesa-utils`.
Container memakai ROS 2 Humble di Ubuntu 22.04; host tidak harus Jammy.
Software Mesa adalah jalur awal tanpa perangkat GPU tambahan.
Wayland/XWayland, SSH X11 forwarding, Intel/AMD DRI, dan NVIDIA **belum diuji
pada desktop Linux nyata**. Gunakan sesi Xorg/X11 saat login untuk jalur awal.

## Cek sesi, siapkan Xauthority, build, start

Semua perintah berikut dari root repo dalam **Bash pada terminal desktop host**:

```bash
uname -m                         # harus x86_64
printf 'session=%s DISPLAY=%s\n' "$XDG_SESSION_TYPE" "$DISPLAY"
# session harus x11, DISPLAY biasanya :0 atau :1
glxinfo -B                       # renderer host
source docker/scripts/linux-x11.sh
docker compose -f docker/linux/compose.yaml config
docker compose -f docker/linux/compose.yaml build
docker compose -f docker/linux/compose.yaml up -d
```

Skrip menyalin cookie display aktif ke `.cache/asv/Xauthority` (mode 600),
mengubah family menjadi wildcard untuk hostname container, lalu mengekspor
`ASV_XAUTHORITY`, `ASV_UID`, dan `ASV_GID`. UID/GID build mengikuti user host agar
file workspace tidak menjadi milik root. Cookie di-mount read-only, bersama
socket `/tmp/.X11-unix`. Tidak perlu `xhost +` atau container privileged.
Jalankan `source` lagi di terminal host baru dan setelah login ulang atau
cookie berganti, sebelum memakai Compose. Jangan membagikan file cookie.

## Renderer, arena, teleop

Dari terminal host, cek akses X11 serta renderer **container**:

```bash
docker compose -f docker/linux/compose.yaml exec asv xdpyinfo >/dev/null
docker compose -f docker/linux/compose.yaml exec asv glxinfo -B
docker compose -f docker/linux/compose.yaml exec asv dbus-run-session -- bash
```

Dalam shell container:

```bash
source /opt/asv/environment.sh
ros2 launch vrx_gz arena.launch.py arena:=1
```

Jendela Gazebo muncul di desktop host. Arena 1: teleop; 2: stereo;
3: lurus; 4: zigzag. Ctrl+C sebelum berpindah arena.
Di terminal host kedua, dari root repo:

```bash
source docker/scripts/linux-x11.sh
docker compose -f docker/linux/compose.yaml exec asv dbus-run-session -- bash
```

Dalam shell kedua:

```bash
cd /workspace/asv_ws
colcon build --merge-install
source /opt/asv/environment.sh
python3 src/asv_stereo/asv_stereo/teleop.py
```

Gunakan panah dan Ctrl+C. Perintah file langsung mempertahankan `setup.py`
lokal yang belum punya console script. Kedua platform memakai `asv_ws/src`
yang sama. Pada arena 2, jalankan `/opt/asv/check-stereo.sh` untuk cek stream.

Default `LIBGL_ALWAYS_SOFTWARE=1`: `glxinfo -B` biasanya menunjukkan llvmpipe.
Renderer host dan container bisa berbeda. Untuk renderer kamera/server Gazebo,
periksa juga log Ogre2 di `~/.gz/rendering/` dalam container; `glxinfo` saja
bukan bukti kamera Gazebo memakai GPU yang sama. Performa llvmpipe bisa lambat.

## GPU opsional — belum diuji pada hardware Linux

Aktifkan satu overlay sesuai perangkat host. Jalankan penyiapan Xauthority di
atas terlebih dahulu. Gunakan pasangan file `-f` yang sama pada perintah
`exec`, `stop`, dan `restart` selanjutnya.

Intel/AMD dengan Mesa dan `/dev/dri` (sesuaikan nama device dengan host):

```bash
ls -l /dev/dri
export ASV_RENDER_GID="$(stat -c '%g' /dev/dri/renderD128)"
export ASV_VIDEO_GID="$(stat -c '%g' /dev/dri/card0)"
docker compose -f docker/linux/compose.yaml -f docker/linux/compose.gpu-dri.yaml up -d --force-recreate
docker compose -f docker/linux/compose.yaml -f docker/linux/compose.gpu-dri.yaml exec asv glxinfo -B
```

NVIDIA memerlukan driver host dan NVIDIA Container Toolkit yang sudah
[dikonfigurasi untuk Docker](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html):

```bash
nvidia-smi
docker compose -f docker/linux/compose.yaml -f docker/linux/compose.gpu-nvidia.yaml up -d --force-recreate
docker compose -f docker/linux/compose.yaml -f docker/linux/compose.gpu-nvidia.yaml exec asv nvidia-smi
docker compose -f docker/linux/compose.yaml -f docker/linux/compose.gpu-nvidia.yaml exec asv glxinfo -B
```

Overlay mematikan pemaksaan software rendering. Periksa renderer yang tampil,
kemudian arena, kamera, dan teleop; keberhasilan `nvidia-smi` saja belum
membuktikan render Gazebo. Untuk kembali ke software, gunakan Compose dasar:

```bash
docker compose -f docker/linux/compose.yaml up -d --force-recreate
```

## Stop, restart, troubleshooting

Dari root repo setelah menyiapkan environment Xauthority:

```bash
docker compose -f docker/linux/compose.yaml logs -f
docker compose -f docker/linux/compose.yaml stop
docker compose -f docker/linux/compose.yaml start
docker compose -f docker/linux/compose.yaml restart
docker compose -f docker/linux/compose.yaml down
```

`restart` tidak meluncurkan arena lagi. `down` menghapus hasil Colcon dalam
container; source tetap di host. Build ulang setelah membuat container baru.

- **Can't open display / authorization required:** cek `echo "$DISPLAY"`,
  `echo "$XAUTHORITY"`, `xauth nlist "$DISPLAY"`, lalu source skrip lagi dari
  terminal sesi X11 yang benar. Jangan menjalankan persiapan sebagai root.
- **Xauthority kosong:** jika desktop memakai file khusus, ekspor `XAUTHORITY`
  ke file sesi yang benar sebelum source; skrip berhenti jika cookie tidak ada.
- **Permission denied pada src atau cookie:** cek `id`, `ASV_UID`, `ASV_GID`;
  rebuild setelah UID/GID berubah dan buat ulang container.
- **Wayland:** login ulang ke sesi Xorg/X11. Konfigurasi ini belum memvalidasi
  jalur Wayland/XWayland.
- **GPU gagal:** kembali ke Compose dasar dan cek llvmpipe. Periksa device,
  group numeric, driver, dan runtime GPU host sebelum mencoba overlay lagi.
- **Fuel gagal saat build:** `PREFETCH_FUEL=0 docker compose -f docker/linux/compose.yaml build`;
  arena kemudian perlu internet untuk mengambil model.
- **Bridge hilang:** `ros2 pkg prefix ros_gz_bridge` dalam shell yang sudah
  source environment. Gunakan paket Garden khusus, jangan bridge Fortress.

Sebelum menandai Linux lulus, tes di desktop nyata: build amd64 native,
`xdpyinfo`, renderer software, arena 1/teleop (thrust dan gerak kapal), arena 2
(kedua kamera + camera_info), stop/restart, dan ulangi tes dengan GPU yang
akan dipakai. Build di OrbStack hanya memvalidasi image amd64 lewat emulasi.
