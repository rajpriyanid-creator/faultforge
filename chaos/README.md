# FaultForge Chaos Network Topology & Port Mapping

This document specifies the network topology, container ports, and address mappings used by the FaultForge chaos test stack.

---

## 1. Network Architecture

All services operate on an isolated bridge network named `chaos-net` defined in `chaos/docker-compose.chaos.yml`:

```
+-------------------------------------------------------------------------------+
| Container Network: chaos-net                                                  |
|                                                                               |
|  +--------------------+        HTTP         +--------------------+            |
|  | app                | ------------------> | toxiproxy          |            |
|  | (:8090)            |                     | (:8082 proxy)      |            |
|  |                    |                     | (:8474 mgmt API)   |            |
|  +--------------------+                     +--------------------+            |
|                                                       |                       |
|                                                       | Upstream Socket       |
|                                                       v                       |
|                                             +--------------------+            |
|                                             | shipping-stub      |            |
|                                             | (:8081 carrier)    |            |
|                                             +--------------------+            |
+-------------------------------------------------------------------------------+
```

---

## 2. Port and URL Reference Matrix

| Service | Container Port | Host Port | In-Network URL (Inter-Container) | External Host / CI Runner URL | Purpose |
|---|---|---|---|---|---|
| **`shipping-stub`** | `8081` | `8081` | `http://shipping-stub:8081` | `http://127.0.0.1:8081` | Mock shipping carrier dependency |
| **`toxiproxy` (Proxy)** | `8082` | `8082` | `http://toxiproxy:8082` | `http://127.0.0.1:8082` | Fault injection socket (upstream -> `shipping-stub:8081`) |
| **`toxiproxy` (API)** | `8474` | `8474` | `http://toxiproxy:8474` | `http://127.0.0.1:8474` | Toxiproxy REST management API |
| **`app`** | `8090` | `8090` | `http://app:8090` | `http://127.0.0.1:8090` | FaultForge checkout microservice under test |

---

## 3. Environment Variable Conventions

- **`SHIPPING_SERVICE_URL`**:
  - In Docker Compose: `http://toxiproxy:8082`
  - In local development (standalone proxy): `http://127.0.0.1:8082`
- **`TOXIPROXY_URL`**:
  - In Docker Compose (from runner/host): `http://127.0.0.1:8474`
  - In inter-container scripts: `http://toxiproxy:8474`
- **`APP_TARGET_URL`**:
  - From CI runner or host probe: `http://127.0.0.1:8090`

---

## 4. Upstream Address Safety

When running inside Docker containers:
- Toxiproxy MUST route upstream traffic to `shipping-stub:8081` (the container DNS service name).
- Using `127.0.0.1:8081` as Toxiproxy's upstream inside a container would improperly loop back to Toxiproxy's own network namespace.
- `chaos/toxiproxy-config.json` explicitly specifies `"upstream": "shipping-stub:8081"`.
