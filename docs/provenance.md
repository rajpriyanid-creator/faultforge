# FaultForge Project Provenance & Path A Compliance

## 1. Overview & Track Declaration
- **Hackathon:** GitLab Transcend — Life After Code (October 2026)
- **Track:** **Path A — Start Fresh**
- **Evaluation Deadline:** October 27, 2026, 1:00 PM UTC (6:30 PM IST)
- **Target Category:** Best Supervised Agent ($4,000)

## 2. Empirical Git History & Commit Provenance

All source code, configuration files, and assets in this repository were created fresh during the official hackathon submission window.

### First Commit (Repository Inception)
Factually extracted from repository `git log --reverse`:

```text
commit b22d2e8587635c9527f7a7d4db1c6e17409fbe7a
Author: FaultForge Agent <agent@faultforge.internal>
Date:   Fri Oct 16 06:25:13 2026 +0530

    feat: initial checkout and resilient shipping client
```

### Commit History Facts
- **First Commit Date:** October 16, 2026, 06:25:13 +05:30 (00:55:13 UTC).
- **Submission Date:** October 2026 (prior to deadline of October 27, 2026, 1:00 PM UTC).
- **Total Commit Count:** Continuous active development spanning October 16–20, 2026.
- **GitLab Showcase Integration:** Commits integrated cleanly with the official hackathon showcase project (`gitlab-ai-hackathon/transcend-october-2026/43424456/showcase`).

## 3. Code Reuse & External Attribution Declaration
In strict adherence to Path A guidelines ("Start Fresh"):
- **Zero Pre-Existing Repository Reuse:** The codebase was not cloned or ported from any pre-existing commercial product, proprietary library, or previous competition entry.
- **Custom Application Layer:** The `checkout-service` (`app/`) and downstream `mock_shipping_api` (`stub/`) are custom lightweight microservices written specifically to model downstream latency degradation.
- **Official Open-Source Ecosystem Components Used:**
  - **Shopify Toxiproxy:** Official binary release `v2.9.0` used as the network chaos engine (MIT License).
  - **GitLab Duo Custom Flows:** Built strictly to the official GitLab Duo Custom Flows Schema v1 (`flows/faultforge-flow.yaml`).
  - **Standard Python Libraries:** FastAPI, Uvicorn, HTTPX, Requests, Pytest, and Bandit (all standard open-source dependencies listed in `requirements.txt`).
