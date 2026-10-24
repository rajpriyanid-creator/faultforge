# SPDX-License-Identifier: MIT
import os
import json
import pytest
from httpx import AsyncClient, ASGITransport
import app.main as main_mod
from app.main import app
from scripts.verify_live_evidence_api import compare_receipts

@pytest.fixture(autouse=True)
def reset_runtime_receipt():
    main_mod._RUNTIME_EVIDENCE_RECEIPT = None
    yield
    main_mod._RUNTIME_EVIDENCE_RECEIPT = None

@pytest.mark.asyncio
async def test_live_evidence_api_matches_sealed_receipt():
    """Verify that JSON served by /api/v1/evidence matches sealed evidence_receipt.json with zero differences."""
    receipt_path = "reports/evidence_receipt.json" if os.path.exists("reports/evidence_receipt.json") else "docs/sample_reports/evidence_receipt.json"
    assert os.path.exists(receipt_path)

    with open(receipt_path, "r", encoding="utf-8") as f:
        sealed_receipt = json.load(f)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # GET returns sealed receipt
        res = await client.get("/api/v1/evidence")
        assert res.status_code == 200
        api_data = res.json()
        assert compare_receipts(api_data, sealed_receipt) is True
        assert api_data == sealed_receipt

        # POST updates runtime receipt
        test_update = dict(sealed_receipt)
        test_update["receipt_id"] = "rcpt-updated-test"
        post_res = await client.post("/api/v1/evidence", json=test_update)
        assert post_res.status_code == 200
        assert post_res.json()["status"] == "STORED"

        # Subsequent GET returns updated receipt
        get_res = await client.get("/api/v1/evidence")
        assert get_res.status_code == 200
        assert get_res.json() == test_update

@pytest.mark.asyncio
async def test_live_evidence_api_rejects_invalid_post():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/v1/evidence", json={"not_a_receipt": True})
        assert res.status_code == 400

def test_compare_receipts_detects_synthesized_or_altered_fields():
    receipt = {
        "receipt_id": "rcpt-test",
        "final_status": "RECOVERED_AND_VERIFIED",
        "probe_count": 20
    }
    # Extra field in API
    altered_api = dict(receipt)
    altered_api["invented_field"] = "fake"
    assert compare_receipts(altered_api, receipt) is False

    # Mismatched value
    altered_val = dict(receipt)
    altered_val["probe_count"] = 99
    assert compare_receipts(altered_val, receipt) is False
