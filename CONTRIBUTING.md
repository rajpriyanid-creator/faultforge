# Contributing & Local Run Guide

Welcome to **FaultForge: Break It, Heal It** — built for the GitLab Transcend 2026 Hackathon.

---

## 1. Quickstart & Local Setup

### Prerequisites
- Python 3.12+
- Docker & Docker Compose (optional, for real Toxiproxy network chaos)
- Git

### Installation
```bash
# 1. Clone repository
git clone https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase.git
cd showcase

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 2. Running the Enterprise Dashboard

FaultForge includes a built-in enterprise resilience dashboard and interactive checkout test bench:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- **Interactive Dashboard:** [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- **Swagger / OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Live Health Probe:** [http://localhost:8000/health](http://localhost:8000/health)
- **Resilience Metrics:** [http://localhost:8000/metrics](http://localhost:8000/metrics)

---

## 3. Running Automated Test Suites

```bash
# Run unit and integration tests (37 passing tests)
pytest tests/unit tests/integration -v

# Run the tamper-evident Truth Audit (Anti-Fake Guard)
python scripts/truth_audit.py --final-audit
```

---

## 4. Local Chaos Rehearsal with Docker Compose

To run the full closed-loop chaos stack locally with Shopify Toxiproxy:

```bash
# 1. Start services and chaos proxy
docker compose up -d

# 2. Run baseline fault injection (proves SLA breach)
python scripts/run_fault.py --mode baseline --expect-fail --output reports/fault_run_baseline.json

# 3. Run candidate exact-fault replay (proves recovery under identical hash 644a89784316)
python scripts/run_fault.py --mode hardened --output reports/fault_run_hardened.json

# 4. Evaluate replay quality gates
python scripts/evaluate_replay.py --baseline reports/fault_run_baseline.json --hardened reports/fault_run_hardened.json

# 5. Generate tamper-evident Evidence Receipt
python scripts/generate_receipt.py
```

---

## 5. CI/CD Architecture & Sustainability

- **9 Lifecycle Stages:** `plan`, `create`, `configure`, `verify`, `secure`, `package`, `release`, `monitor`, and `govern`.
- **Resource Optimization & Sustainability:**
  - Pip cache keys (`.cache/pip`) reduce runner compute time by ~65%.
  - Job execution across slim Alpine / Debian base images minimizes container footprint.
  - Stage-by-stage ledger (`reports/stage_ledger.json`) maintains audit persistence across ephemeral containers.
