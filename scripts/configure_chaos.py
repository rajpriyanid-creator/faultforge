#!/usr/bin/env python3
import os
import sys
import json
import hashlib
import requests
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from chaos.toxiproxy_helper import ToxiproxyClient

def configure_chaos_network(
    profile_path: str = "chaos/profiles/latency_cascading_hang.json",
    toxi_api: str = os.getenv("TOXIPROXY_URL", "http://127.0.0.1:8474"),
    output_path: str = "reports/fault_config.json"
) -> Dict[str, Any]:
    if not os.path.exists(profile_path):
        print(f"[-] Profile missing: {profile_path}", file=sys.stderr)
        sys.exit(1)

    with open(profile_path, "r", encoding="utf-8") as f:
        profile = json.load(f)

    client = ToxiproxyClient(toxi_api)
    proxy_name = profile.get("proxy_name", "shipping_api_proxy")
    listen = profile.get("listen", "0.0.0.0:8082")
    upstream = profile.get("upstream", "127.0.0.1:8081")
    fault_type = profile.get("fault_type", "latency")
    attrs = profile.get("attributes", {})

    print(f"[*] Configuring Toxiproxy via {toxi_api} ...")
    if not client.is_available():
        print(f"[-] Error: Toxiproxy is unreachable at {toxi_api}", file=sys.stderr)
        sys.exit(1)

    client.setup_proxy(proxy_name, listen, upstream)
    client.add_toxic(proxy_name, fault_type, attrs)

    readback = client.get_toxic(proxy_name, f"{fault_type}_toxic")
    canonical = json.dumps(readback, sort_keys=True)
    config_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]

    config_record = {
        "status": "APPLIED",
        "proxy_name": proxy_name,
        "listen": listen,
        "upstream": upstream,
        "fault_type": fault_type,
        "attributes": readback.get("attributes", attrs),
        "config_hash": config_hash
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(config_record, f, indent=2)

    print(f"[+] Toxiproxy fault configured. Saved to {output_path} (Hash: {config_hash})")
    return config_record

if __name__ == "__main__":
    configure_chaos_network()
