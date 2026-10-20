#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
FaultForge Toxiproxy Daemon Bootstrapper
Ensures the official Shopify Toxiproxy server (v2.9.0) is running locally
for both CI/CD runners and local execution environments.
"""
import os
import sys
import time
import shutil
import platform
import subprocess
import urllib.request
from typing import Optional

TOXIPROXY_VERSION = "2.9.0"
BASE_DOWNLOAD_URL = f"https://github.com/Shopify/toxiproxy/releases/download/v{TOXIPROXY_VERSION}"

def is_toxiproxy_running(url: str = "http://127.0.0.1:8474") -> Optional[str]:
    try:
        req = urllib.request.Request(f"{url.rstrip('/')}/version")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                return resp.read().decode("utf-8").strip()
    except Exception:
        pass
    return None

def get_binary_target() -> (str, str):
    system = platform.system().lower()
    machine = platform.machine().lower()
    ext = ".exe" if system == "windows" else ""

    arch = "amd64"
    if machine in ("arm64", "aarch64"):
        arch = "arm64"
    elif machine in ("x86_64", "amd64"):
        arch = "amd64"

    if system == "linux":
        bin_name = f"toxiproxy-server-linux-{arch}"
    elif system == "darwin":
        bin_name = f"toxiproxy-server-darwin-{arch}"
    elif system == "windows":
        bin_name = "toxiproxy-server-windows-amd64.exe"
    else:
        bin_name = f"toxiproxy-server-linux-amd64"

    local_name = f"toxiproxy-server{ext}"
    return bin_name, local_name

def find_or_download_binary() -> str:
    # 1. Check system PATH
    sys_path = shutil.which("toxiproxy-server") or shutil.which("toxiproxy-server.exe")
    if sys_path and os.path.isfile(sys_path):
        return sys_path

    remote_name, local_name = get_binary_target()

    # 2. Check local directories
    candidate_dirs = [
        os.path.join(os.getcwd(), "bin"),
        os.path.expanduser("~/.cache/toxiproxy"),
        "/usr/local/bin",
        "/tmp"
    ]

    for cdir in candidate_dirs:
        cand = os.path.join(cdir, local_name)
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand

    # 3. Download binary
    download_dir = candidate_dirs[0]
    try:
        os.makedirs(download_dir, exist_ok=True)
    except Exception:
        download_dir = candidate_dirs[1]
        os.makedirs(download_dir, exist_ok=True)

    target_path = os.path.join(download_dir, local_name)
    download_url = f"{BASE_DOWNLOAD_URL}/{remote_name}"
    print(f"[*] Downloading official Shopify Toxiproxy v{TOXIPROXY_VERSION} from {download_url} ...")

    req = urllib.request.Request(download_url, headers={"User-Agent": "FaultForge-CI/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp, open(target_path, "wb") as out_f:
        shutil.copyfileobj(resp, out_f)

    if platform.system().lower() != "windows":
        os.chmod(target_path, 0o755)

    print(f"[+] Downloaded Toxiproxy binary to {target_path}")
    return target_path

def start_toxiproxy(host: str = "0.0.0.0", port: int = 8474) -> bool:
    api_url = f"http://127.0.0.1:{port}"
    existing_ver = is_toxiproxy_running(api_url)
    if existing_ver:
        print(f"[+] Toxiproxy is already running at {api_url} (Version: {existing_ver})")
        return True

    binary_path = find_or_download_binary()
    print(f"[*] Launching Toxiproxy server ({binary_path}) on {host}:{port} ...")

    cmd = [binary_path, "-host", host, "-port", str(port)]
    # Start as detached background process
    if platform.system().lower() == "windows":
        creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0x00000010)
        subprocess.Popen(cmd, creationflags=creationflags)
    else:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

    # Wait for ready
    print(f"[*] Waiting for Toxiproxy API to become healthy at {api_url} ...")
    for _ in range(20):
        time.sleep(0.5)
        ver = is_toxiproxy_running(api_url)
        if ver:
            print(f"[+] Official Shopify Toxiproxy server is live and verified! (Version: {ver})")
            return True

    print(f"[-] Error: Toxiproxy failed to respond on {api_url} within 10 seconds.", file=sys.stderr)
    return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description="FaultForge Toxiproxy Bootstrapper")
    parser.add_argument("--host", default="0.0.0.0", help="Listen host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8474, help="Listen port (default: 8474)")
    args = parser.parse_args()

    success = start_toxiproxy(host=args.host, port=args.port)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
