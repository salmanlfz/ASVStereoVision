# Verifikasi lokal

Host: Mac Apple Silicon, Docker context `orbstack`, engine aarch64.
Target kedua image: linux/amd64 (emulasi di host ini). Dikerjakan 21 November 2026.

## Pemeriksaan konfigurasi

- `docker compose -f docker/mac/compose.yaml config`: lulus.
- `DISPLAY=:0 ASV_XAUTHORITY=/tmp/asv-test.Xauthority docker compose -f docker/linux/compose.yaml config`: lulus parsing; nilai display/cookie adalah placeholder, tidak dipakai sebagai tes desktop.
- Override build Mac serta overlay GPU DRI/NVIDIA: lulus `compose config` dengan variabel pengujian.
- JSON Compose: build context kedua platform tepat di root repo; Dockerfile tersedia; bind source tepat `ROOT/asv_ws/src`, target `/workspace/asv_ws/src`.
- Bash syntax semua skrip: lulus. Syntax Python diagnostik: lulus. Workflow YAML/matrix mac+linux: lulus parse PyYAML; workflow GitHub Actions belum dijalankan.
- Helper Xauthority diuji dengan cookie sintetis pada container Linux: copy cookie, family `ffff`, mode 600, ekspor UID/GID lulus. Penolakan host Mac juga diperiksa. Ini bukan tes autentikasi X11 desktop nyata.
- SHA-256 `package.xml`, `setup.py`, `teleop.py`, `stereo_vision.py`, `asv_otonom.py`, dan `__init__.py` sama dengan sebelum perubahan. Kode ROS lokal tidak diedit.

## Baseline dengan image Mac lokal yang sudah tersedia

Image awal `asv-humble-garden:0.2.0` (`5e968f2ab992`) dijalankan menggunakan
Compose Mac yang sudah dipindah. Ini berbeda dari image hasil rebuild.

- Startup `up -d --no-build --wait`: healthy.
- Browser Chrome benar-benar Connect ke noVNC melalui `127.0.0.1:6080` dan menampilkan MATE.
- Garden 7.9.0, bridge `ros_gz_bridge`, Colcon `asv_stereo`: lulus.
- `glxinfo -B`: llvmpipe LLVM 15.0.7, OpenGL 4.5, Mesa 23.2.1; software rendering.
- Arena 1: `/clock` diterima. GUI dari `docker exec` awalnya tidak tampil; peluncuran melalui `dbus-run-session -- ros2 launch vrx_gz arena.launch.py arena:=1` menampilkan arena dan kapal dalam browser. Viewport sempat putih selama inisialisasi.
- Kedua image_raw dan kedua camera_info: header diterima melalui `/opt/asv/check-stereo.sh` pada arena 1; ada pesan lost pada salah satu stream, jadi ini bukan pengujian performa/frame rate.
- Teleop asli melalui PTY dan subscriber ROS: panah atas menghasilkan thrust kiri/kanan 1000.0, idle 0.0, Ctrl+C keluar bersih (53 pesan per sisi). Gerak kapal akibat input belum diukur.
- Tes vision pada image awal gagal: NumPy 2.2.6 tidak kompatibel dengan OpenCV/cv_bridge binary. Perbaikan NumPy 1.26.4 yang sudah ada pada Dockerfile lokal dipertahankan dalam skrip bersama; image awal belum memuat perbaikan lokal tersebut.
- Container baseline dihentikan setelah pengujian.

## Image hasil rebuild

### Mac — lulus build dan smoke test

- Build lewat `docker compose -f docker/mac/compose.yaml build asv`: selesai, termasuk 5 paket VRX, prefetch Fuel, dan pemeriksaan vision.
- Image: `sha256:dafd64ead67023e0659c5bcf33f13f2cc4dc46e48c02d865641cceead651fdd0`, linux/amd64; label VRX sesuai commit di atas. Entrypoint asli Tiryoh tetap `/bin/bash -c /entrypoint.sh`.
- Container hasil recreate: healthy; restart dilanjutkan `up --wait` juga kembali healthy. Browser benar-benar Connect ke desktop baru dan menampilkan arena 1 beserta kapal/lingkungan.
- `gz sim --versions`: 7.9.0; bridge ditemukan; `colcon build --merge-install`: 1 paket `asv_stereo` selesai.
- NumPy 1.26.4, OpenCV 4.5.4, dan konversi BGR→RGB melalui cv_bridge: lulus saat build dan runtime sebagai ubuntu. Kegagalan ABI pada image awal teratasi.
- Renderer runtime: llvmpipe LLVM 15.0.7, Mesa 23.2.1, OpenGL 4.5; bukan tes GPU.
- Arena 1 via D-Bus: clock diterima, kedua image_raw dan kedua camera_info diterima. Lost message tetap muncul pada pengamatan kamera kanan; performa real-time/frame rate tidak dinyatakan lulus.
- Teleop asli via PTY: kedua thrust mencapai 1000.0 saat panah atas, kembali 0.0 saat idle; Ctrl+C bersih, 79 pesan per sisi. Gerak kapal akibat teleop belum diukur.

### Linux

Build awal amd64 via emulasi OrbStack selesai. Build ulang konfigurasi final
dihentikan saat instalasi NumPy setelah pengguna membatasi pekerjaan ke penyiapan
konfigurasi. Perubahan terakhir penanganan UID/GID belum selesai diverifikasi
dengan build penuh. Tidak ada smoke test runtime Linux yang dijalankan.
Validasi Compose dan jalur build/mount sudah lulus. Tidak ada build tambahan
yang dibiarkan berjalan dari pekerjaan ini.

## Yang masih harus diuji di Linux desktop nyata

- Build amd64 native, cookie dari sesi Xorg nyata, `xdpyinfo`, dan `glxinfo -B` container.
- Jendela Gazebo tampil pada host, arena 1, teleop dan gerak kapal, arena 2 serta stream kamera.
- Stop/start/restart, cookie baru setelah login ulang, dan permission file workspace untuk UID/GID host.
- Intel/AMD DRI dan NVIDIA: perangkat, group, runtime, renderer OpenGL/Ogre2, dan kamera. Tidak ada hardware Linux GPU yang diuji di host ini.
- Wayland/XWayland dan SSH forwarding belum diuji; target awal tetap X11 lokal.

CI Linux menggunakan Xvfb di dalam container hanya untuk smoke test. Itu tidak
menggantikan pengujian X11/Xauthority maupun GPU pada desktop Linux nyata.
