import os
import json
import time
import socket
import select
import random
import logging
import threading
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger("faultforge.chaos")

class ToxiproxyClient:
    """Client for the official Shopify Toxiproxy REST API (port 8474)."""
    def __init__(self, api_url: str = "http://127.0.0.1:8474"):
        self.api_url = api_url.rstrip("/")

    def get_version(self) -> str:
        try:
            r = requests.get(f"{self.api_url}/version", timeout=1.0)
            if r.status_code == 200:
                return r.text.strip()
        except Exception:
            pass
        return "unknown"

    def get_toxic(self, proxy_name: str, toxic_name: str) -> Dict[str, Any]:
        try:
            r = requests.get(f"{self.api_url}/proxies/{proxy_name}/toxics/{toxic_name}", timeout=1.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return {}

    def is_available(self) -> bool:
        try:
            r = requests.get(f"{self.api_url}/version", timeout=1.0)
            return r.status_code == 200
        except Exception:
            return False

    def setup_proxy(self, name: str, listen: str, upstream: str) -> bool:
        # Check if proxy exists
        try:
            r = requests.get(f"{self.api_url}/proxies/{name}", timeout=1.0)
            if r.status_code == 200:
                return True
        except Exception:
            pass

        payload = {"name": name, "listen": listen, "upstream": upstream, "enabled": True}
        try:
            r = requests.post(f"{self.api_url}/proxies", json=payload, timeout=2.0)
            return r.status_code in (200, 201)
        except Exception as exc:
            logger.error(f"Failed to create Toxiproxy proxy: {exc}")
            return False

    def add_toxic(self, proxy_name: str, toxic_type: str, attributes: Dict[str, Any], toxicity: float = 1.0) -> bool:
        payload = {
            "name": f"{toxic_type}_toxic",
            "type": toxic_type,
            "stream": "downstream",
            "toxicity": toxicity,
            "attributes": attributes
        }
        try:
            r = requests.post(f"{self.api_url}/proxies/{proxy_name}/toxics", json=payload, timeout=2.0)
            return r.status_code in (200, 201)
        except Exception as exc:
            logger.error(f"Failed to add toxic: {exc}")
            return False

    def reset(self, proxy_name: Optional[str] = None):
        try:
            if proxy_name:
                requests.post(f"{self.api_url}/reset", timeout=2.0)
            else:
                requests.post(f"{self.api_url}/reset", timeout=2.0)
        except Exception as exc:
            logger.warning(f"Failed to reset Toxiproxy: {exc}")


class StandaloneChaosProxy:
    """
    Built-in high fidelity Chaos Proxy implementing identical Toxiproxy semantics
    without requiring external binary installations. Supports latency, jitter, and connection resets.
    """
    def __init__(self, listen_host: str = "127.0.0.1", listen_port: int = 8082,
                 upstream_host: str = "127.0.0.1", upstream_port: int = 8081):
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.upstream_host = upstream_host
        self.upstream_port = upstream_port
        self.running = False
        self.server_socket: Optional[socket.socket] = None
        self.thread: Optional[threading.Thread] = None

        # Fault controls
        self.latency_ms: float = 0.0
        self.jitter_ms: float = 0.0
        self.reset_peer: bool = False

    def configure_fault(self, latency_ms: float = 0.0, jitter_ms: float = 0.0, reset_peer: bool = False):
        self.latency_ms = latency_ms
        self.jitter_ms = jitter_ms
        self.reset_peer = reset_peer
        logger.info(f"Chaos proxy updated: latency={latency_ms}ms, jitter={jitter_ms}ms, reset_peer={reset_peer}")

    def reset_faults(self):
        self.latency_ms = 0.0
        self.jitter_ms = 0.0
        self.reset_peer = False
        logger.info("Chaos proxy faults cleared to baseline passthrough")

    def start(self):
        if self.running:
            return
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.listen_host, self.listen_port))
        self.server_socket.listen(50)
        self.running = True

        self.thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.thread.start()
        logger.info(f"Standalone Chaos Proxy running on {self.listen_host}:{self.listen_port} -> {self.upstream_host}:{self.upstream_port}")

    def _accept_loop(self):
        while self.running:
            try:
                client_sock, _ = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client_sock,), daemon=True).start()
            except Exception:
                break

    def _handle_client(self, client_sock: socket.socket):
        upstream_sock = None
        try:
            if self.reset_peer:
                # Immediately reset connection
                client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b'\x01\x00\x00\x00\x00\x00\x00\x00')
                client_sock.close()
                return

            # Apply controlled latency & jitter
            if self.latency_ms > 0:
                jitter = random.uniform(-self.jitter_ms, self.jitter_ms) if self.jitter_ms > 0 else 0
                delay_sec = max(0.0, (self.latency_ms + jitter) / 1000.0)
                time.sleep(delay_sec)

            upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            upstream_sock.connect((self.upstream_host, self.upstream_port))

            # Bi-directional stream forwarding
            sockets = [client_sock, upstream_sock]
            while self.running:
                readable, _, exceptional = select.select(sockets, [], sockets, 0.5)
                if exceptional:
                    break
                for s in readable:
                    data = s.recv(16384)
                    if not data:
                        return
                    if s is client_sock:
                        upstream_sock.sendall(data)
                    else:
                        client_sock.sendall(data)
        except Exception:
            pass
        finally:
            try:
                client_sock.close()
            except Exception:
                pass
            if upstream_sock:
                try:
                    upstream_sock.close()
                except Exception:
                    pass

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        logger.info("Standalone Chaos Proxy stopped.")


class ChaosEngine:
    """Unified engine selecting either native Toxiproxy or Standalone Chaos Proxy."""
    def __init__(self, toxiproxy_api: Optional[str] = None):
        if toxiproxy_api is None:
            toxiproxy_api = os.getenv("TOXIPROXY_URL", "http://127.0.0.1:8474")
        self.toxi_client = ToxiproxyClient(toxiproxy_api)
        self.standalone = StandaloneChaosProxy()
        connected = False
        for _ in range(5):
            if self.toxi_client.is_available():
                connected = True
                break
            time.sleep(0.5)
        self.use_toxi = connected

    def start(self):
        if not self.use_toxi:
            self.standalone.start()

    def apply_profile(self, profile: Dict[str, Any]):
        fault_type = profile.get("fault_type", "latency")
        attrs = profile.get("attributes", {})

        if self.use_toxi:
            proxy_name = profile.get("proxy_name", "shipping_api_proxy")
            listen = profile.get("listen", "0.0.0.0:8082")
            upstream = profile.get("upstream", "127.0.0.1:8081")
            self.toxi_client.setup_proxy(proxy_name, listen, upstream)
            self.toxi_client.add_toxic(proxy_name, fault_type, attrs)
        else:
            if fault_type == "latency":
                latency = attrs.get("latency", 3500)
                jitter = attrs.get("jitter", 250)
                self.standalone.configure_fault(latency_ms=latency, jitter_ms=jitter, reset_peer=False)
            elif fault_type in ("reset_peer", "reset"):
                self.standalone.configure_fault(reset_peer=True)

    def get_version(self) -> str:
        if self.use_toxi:
            return self.toxi_client.get_version()
        return "standalone"

    def read_back_toxic(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        if self.use_toxi:
            proxy_name = profile.get("proxy_name", "shipping_api_proxy")
            toxic_type = profile.get("fault_type", "latency")
            toxic_name = f"{toxic_type}_toxic"
            toxic_data = self.toxi_client.get_toxic(proxy_name, toxic_name)
            return toxic_data.get("attributes", toxic_data)
        else:
            return {
                "latency": self.standalone.latency_ms,
                "jitter": self.standalone.jitter_ms
            }

    def clear(self):
        if self.use_toxi:
            self.toxi_client.reset()
        else:
            self.standalone.reset_faults()

    def stop(self):
        if not self.use_toxi:
            self.standalone.stop()
