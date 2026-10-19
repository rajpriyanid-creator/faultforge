#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
set -euo pipefail

# FaultForge Cloud Run Deployment Script
# Enables versioned candidate revision deployment and traffic splitting

PROJECT_ID="${GCP_PROJECT_ID:-faultforge-hackathon}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-faultforge-checkout}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}"

echo "=========================================================="
echo " Deploying ${SERVICE_NAME} to Google Cloud Run (${REGION})"
echo " Image: ${IMAGE}"
echo "=========================================================="

# 1. Build & Push Image
echo "[*] Building container image..."
docker build -t "${IMAGE}" .
docker push "${IMAGE}"

# 2. Deploy Candidate Revision with NO Immediate Production Traffic (0%)
echo "[*] Deploying candidate revision..."
CANDIDATE_REV=$(gcloud run deploy "${SERVICE_NAME}" \
  --image="${IMAGE}" \
  --region="${REGION}" \
  --platform=managed \
  --no-traffic \
  --format="value(status.latestCreatedRevisionName)")

echo "[+] Candidate revision created: ${CANDIDATE_REV}"

# 3. Health Smoke Check
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --region="${REGION}" --format="value(status.url)")
echo "[*] Running health smoke check against candidate..."
python3 scripts/cloudrun_traffic.py --action verify --url "${SERVICE_URL}"

# 4. Route Canary Traffic (10% Candidate, 90% Stable)
echo "[*] Updating canary traffic split: 10% to ${CANDIDATE_REV}..."
python3 scripts/cloudrun_traffic.py --action route --service "${SERVICE_NAME}" --region "${REGION}" --revisions="${CANDIDATE_REV}=10"

echo "[+] Canary deployment successful. Ready for Supervised promotion gate."
