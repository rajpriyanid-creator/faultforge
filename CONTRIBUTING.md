# CONTRIBUTING.md — Contribution & Developer Run Guide
# SPDX-License-Identifier: MIT

Welcome to **FaultForge: Break It, Heal It** — built for the GitLab Transcend 2026 Hackathon.

---

## 1. Quickstart & Local Setup

### Prerequisites
- Python 3.12+
- Git
- (Optional) Docker & Docker Compose (for Shopify Toxiproxy and containerized testing)

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

## 2. Running Locally Without Docker or GCP

You can run the entire test suite and verify the API and resilience dashboard without Docker or GCP:

```bash
# 1. Run unit and integration tests (52 passing tests)
pytest tests/unit tests/integration tests/test_*.py -v

# 2. Run the anti-fake Truth Audit in strict final mode
python scripts/truth_audit.py --final-audit

# 3. Launch the resilience web dashboard locally
python -m uvicorn app.main:app --host 127.0.0.1 --port 8090
# Open http://127.0.0.1:8090/dashboard in your browser
```

---

## 3. Running Local Supervised Gate (No GCP Required)

If evaluating the Supervised Human Gate and instant rollback without Google Cloud credentials:

```bash
# Start local supervised staging stack (checkout-service, toxiproxy, gate)
./scripts/local_gate.sh start
# (On Windows, run: python scripts/local_gate.py --action start)

# Check gate status (Status: BLOCKED_PENDING_APPROVAL)
./scripts/local_gate.sh status

# Simulate human sign-off (Status: PROMOTED)
./scripts/local_gate.sh approve

# Or simulate instant rollback (reverts candidate container to stable)
./scripts/local_gate.sh rollback

# Clean up
./scripts/local_gate.sh stop
```

---

## 4. Running with Google Cloud Run (GCP Bonus)

To verify the live Google Cloud Run deployment in `us-central1`:

```bash
# Verify live endpoints
curl -sf https://faultforge-checkout-136942862703.us-central1.run.app/health
curl -sf https://faultforge-checkout-136942862703.us-central1.run.app/api/v1/evidence

# Simulate candidate deployment & rollback using scripts/cloudrun_traffic.py
python scripts/cloudrun_traffic.py --action rollback --dry-run
```

Deployment manifests are located in `infra/cloudrun/service.yaml`.

---

## 5. Submitting Issues and Merge Requests

We welcome contributions and bug reports!

1. **Security & Guardrails:** Never alter authentication, payment processing, database schemas, secrets, or IAM policies automatically. All changes must comply with [`chaos/risk-policy.json`](chaos/risk-policy.json).
2. **Deterministic Replay:** Any resilience change must include a regression test in `tests/chaos/test_resilience.py` and pass exact-fault replay under Toxiproxy profile hash `644a89784316`.
3. **Branching & Commits:**
   - Create a feature branch: `git checkout -b feature/your-enhancement`
   - Ensure all tests pass: `pytest tests/unit tests/integration -v`
   - Run truth audit: `python scripts/truth_audit.py --final-audit`
   - Open a GitLab Merge Request targeting `main`.

---

## 6. Secrets Handling Policy

- **Zero Hardcoded Secrets:** Tokens, API keys, passwords, private certificates, and credentials must never be committed to git, logged in CI outputs, or embedded in Docker images.
- **GitLab CI/CD Variables:** All secrets (such as `FF_GITLAB_TOKEN`, `GCP_PROJECT`, and `GCP_SA_KEY`) must strictly reside in GitLab project settings (**Settings → CI/CD → Variables**), configured as **Masked** and **Protected**.
- **Local Development:** Store secrets only in uncommitted `.env` files (excluded by `.gitignore` and `.dockerignore`). Never commit `.env` or credentials JSON files.
