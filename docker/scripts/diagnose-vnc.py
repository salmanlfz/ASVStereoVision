#!/usr/bin/env python3
"""Read-only checks from the Mac through the published port to TigerVNC."""
import base64
import hashlib
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def run(args, timeout=20):
    print("\n$ " + " ".join(args), flush=True)
    try:
        p = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=timeout)
        print(p.stdout, flush=True)
        return p.stdout if p.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(str(exc), flush=True)
        return None


def exact(sock, n):
    result = b""
    while len(result) < n:
        chunk = sock.recv(n - len(result))
        if not chunk:
            raise RuntimeError("Connection closed before RFB data arrived")
        result += chunk
    return result


def websocket_rfb(host, port):
    # Use a real WebSocket upgrade and masked client frames, not a TCP-only probe.
    with socket.create_connection((host, port), timeout=5) as sock:
        sock.settimeout(5)
        key = base64.b64encode(os.urandom(16)).decode()
        request = (f"GET /websockify HTTP/1.1\r\nHost: {host}:{port}\r\n"
                   f"Origin: http://{host}:{port}\r\nUpgrade: websocket\r\n"
                   f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
                   "Sec-WebSocket-Version: 13\r\n"
                   "Sec-WebSocket-Protocol: binary\r\n\r\n")
        sock.sendall(request.encode())
        header = b""
        while not header.endswith(b"\r\n\r\n"):
            header += exact(sock, 1)
            if len(header) > 65536:
                raise RuntimeError("Oversized upgrade response")
        print(header.decode(errors="replace").strip())
        lines = header.decode().split("\r\n")
        if lines[0].split()[1] != "101":
            raise RuntimeError("WebSocket upgrade failed")
        headers = dict(line.split(":", 1) for line in lines[1:] if ":" in line)
        headers = {k.lower(): v.strip() for k, v in headers.items()}
        expected = base64.b64encode(hashlib.sha1(
            (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        if headers.get("sec-websocket-accept") != expected:
            raise RuntimeError("Invalid WebSocket accept value")
        if headers.get("sec-websocket-protocol", "binary") != "binary":
            raise RuntimeError("Server did not select binary WebSocket transport")

        def send(payload, opcode=2):
            mask = os.urandom(4)
            if len(payload) > 125:
                raise RuntimeError("Probe client frame too large")
            sock.sendall(bytes([0x80 | opcode, 0x80 | len(payload)]) + mask +
                         bytes(v ^ mask[i % 4] for i, v in enumerate(payload)))

        buffered = bytearray()

        def read(n):
            while len(buffered) < n:
                first, second = exact(sock, 2)
                size = second & 127
                if size == 126:
                    size = struct.unpack("!H", exact(sock, 2))[0]
                elif size == 127:
                    size = struct.unpack("!Q", exact(sock, 8))[0]
                if size > 16 * 1024 * 1024:
                    raise RuntimeError("Oversized WebSocket frame")
                mask = exact(sock, 4) if second & 128 else None
                payload = exact(sock, size)
                if mask:
                    payload = bytes(v ^ mask[i % 4] for i, v in enumerate(payload))
                opcode = first & 15
                if opcode == 8:
                    raise RuntimeError(f"WebSocket closed: {payload!r}")
                if opcode == 9:
                    send(payload, 10)
                elif opcode in (0, 2):
                    buffered.extend(payload)
                elif opcode == 1:
                    raise RuntimeError("Received text instead of binary RFB transport")
            result = bytes(buffered[:n])
            del buffered[:n]
            return result

        banner = read(12)
        print(f"RFB through WebSocket from Mac: {banner!r}")
        if banner not in (b"RFB 003.008\n", b"RFB 003.007\n", b"RFB 003.003\n"):
            raise RuntimeError("Unexpected RFB version; probe supports RFB 3.3/3.7/3.8")
        send(banner)
        legacy = banner == b"RFB 003.003\n"
        count = struct.unpack("!I", read(4))[0] if legacy else read(1)[0]
        if count == 0:
            length = struct.unpack("!I", read(4))[0]
            if length > 65536:
                raise RuntimeError("Oversized RFB rejection reason")
            raise RuntimeError(f"RFB rejected connection: {read(length).decode(errors='replace')}")
        security = [count] if legacy else list(read(count))
        print(f"RFB security types: {security} (1=None, 2=VNC password)")
        if 1 not in security:
            print("RFB transport PASS; authentication required; no password attempted.")
            return
        if not legacy:
            send(b"\x01")
        if banner == b"RFB 003.008\n" and read(4) != b"\0\0\0\0":
            raise RuntimeError("RFB authentication failed")
        send(b"\x01")  # Shared session: do not disconnect existing desktop users.
        initial = read(24)
        width, height = struct.unpack("!HH", initial[:4])
        length = struct.unpack("!I", initial[20:24])[0]
        if length > 65536:
            raise RuntimeError("Oversized desktop name")
        print(f"RFB ServerInit PASS: {width}x{height}, {read(length).decode(errors='replace')}")
        send(b"", 8)


def main():
    print(f"Project: {ROOT}; .env exists: {(ROOT / '.env').exists()}")
    run(["docker", "context", "show"])
    run(["docker", "context", "ls"])
    config = run(["docker", "compose", "-f", "docker/mac/compose.yaml", "config", "--format", "json"])
    if not config:
        return 1
    service = json.loads(config)["services"]["asv"]
    ports = [p for p in service.get("ports", []) if p["target"] == 80]
    if not ports:
        print("No port mapping to container port 80")
        return 1
    host = ports[0].get("host_ip", "127.0.0.1")
    host = "127.0.0.1" if host == "0.0.0.0" else host
    port = int(ports[0]["published"])
    run(["docker", "compose", "-f", "docker/mac/compose.yaml", "ps", "-a"])
    run(["docker", "ps", "-a", "--format", "{{.ID}} {{.Image}} {{.Names}} {{.Ports}}"])
    cid = run(["docker", "compose", "-f", "docker/mac/compose.yaml", "ps", "-q", "asv"])
    if cid and cid.strip():
        run(["docker", "inspect", "--format",
             "Image={{.Config.Image}} ID={{.Image}} Entrypoint={{json .Config.Entrypoint}} Cmd={{json .Config.Cmd}} Ports={{json .NetworkSettings.Ports}} State={{json .State}}",
             cid.strip()])
    run(["docker", "image", "inspect", "--format",
         'ID={{.Id}} Platform={{.Os}}/{{.Architecture}} Entrypoint={{json .Config.Entrypoint}} Cmd={{json (index .Config "Cmd")}}', service["image"]])
    run(["docker", "compose", "-f", "docker/mac/compose.yaml", "logs", "--no-color", "--tail", "100", "asv"])
    run(["docker", "compose", "-f", "docker/mac/compose.yaml", "exec", "-T", "asv", "bash", "-lc",
         "ps -eo pid,user,args | grep -E 'vnc|websockify|mate|supervisor' | grep -v grep; "
         "ss -ltnp; "
         "source /opt/asv/environment.sh; "
         "ros2 pkg prefix vrx_gz; ros2 pkg prefix ros_gz_bridge; "
         "find /home -maxdepth 3 -name '*.log' -path '*/.vnc/*' -exec tail -n 40 {} \\;"])
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for path in ("/", "/vnc.html", "/app/ui.js"):
        try:
            with opener.open(f"http://{host}:{port}{path}", timeout=5) as response:
                body = response.read()
                print(f"HTTP {path}: {response.status}, {response.headers.get('Content-Type')}, "
                      f"bytes={len(body)}, sha256={hashlib.sha256(body).hexdigest()}")
                if path == "/app/ui.js":
                    lines = body.decode(errors="replace").splitlines()
                    print("ui.js lines 225–245:\n" + "\n".join(lines[224:245]))
        except Exception as exc:
            print(f"HTTP {path}: FAIL {exc}")
    try:
        websocket_rfb(host, port)
    except Exception as exc:
        print(f"WebSocket/RFB FAIL: {exc}")
        run(["docker", "compose", "-f", "docker/mac/compose.yaml", "logs", "--no-color", "--tail", "40", "asv"])
        return 1
    run(["docker", "compose", "-f", "docker/mac/compose.yaml", "logs", "--no-color", "--tail", "40", "asv"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
