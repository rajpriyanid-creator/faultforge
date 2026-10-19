# SPDX-License-Identifier: MIT
# Copyright (c) 2026 FaultForge Authors

import os
import json
import re
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

DEFAULT_TARGET_URL = os.getenv("TARGET_URL", "https://faultforge-checkout-136942862703.us-central1.run.app")

@pytest.fixture(scope="session")
def base_url():
    return DEFAULT_TARGET_URL.rstrip("/")

def test_web_dashboard_title_and_branding(page: Page, base_url: str):
    """Validate dashboard page title, branding mark, and navigation strip."""
    page.goto(f"{base_url}/dashboard", wait_until="networkidle")
    
    # 1. Page Title & Meta
    expect(page).to_have_title(re.compile("FaultForge", re.IGNORECASE))
    
    # 2. Brand Mark & Title
    logo = page.locator("header div:has-text('FF')").first
    expect(logo).to_be_visible()
    title_span = page.locator("header span:has-text('FaultForge')").first
    expect(title_span).to_be_visible()
    
    # 3. Autonomy Badge
    autonomy_badge = page.locator("header span:has-text('SUPERVISED AUTONOMY')")
    expect(autonomy_badge).to_be_visible()
    
    # 4. OpenAPI / Swagger Link
    swagger_link = page.locator("header a[href='/docs']")
    expect(swagger_link).to_be_visible()
    
    # 5. GitLab Pipeline Link in Header
    pipeline_link = page.locator("#nav-pipeline-link")
    expect(pipeline_link).to_be_visible()
    expect(pipeline_link).to_have_attribute("href", re.compile(r"gitlab\.com/.+/pipelines/\d+"))
    expect(pipeline_link).to_contain_text("GitLab Pipeline #2963430484")

def test_web_dashboard_kpis_and_metrics_polling(page: Page, base_url: str):
    """Validate live KPI bar metrics: Health status, Circuit Breaker, Requests."""
    page.goto(f"{base_url}/dashboard", wait_until="networkidle")
    
    # 1. Service Status KPI
    status_el = page.locator("#kpi-service-status")
    expect(status_el).to_be_visible()
    expect(status_el).to_have_text("HEALTHY")
    
    # 2. Uptime KPI
    uptime_el = page.locator("#kpi-uptime")
    expect(uptime_el).to_be_visible()
    expect(uptime_el).to_contain_text("s")
    
    # 3. Circuit Breaker State & Fails
    cb_state_el = page.locator("#kpi-cb-state")
    expect(cb_state_el).to_be_visible()
    expect(cb_state_el).to_have_text("CLOSED")
    
    cb_fails_el = page.locator("#kpi-cb-fails")
    expect(cb_fails_el).to_be_visible()
    expect(cb_fails_el).to_have_text("0 / 3")
    
    # 4. Total Requests & Latency KPIs
    total_reqs_el = page.locator("#kpi-total-reqs")
    expect(total_reqs_el).to_be_visible()
    p95_el = page.locator("#kpi-p95")
    expect(p95_el).to_be_visible()

def test_web_dashboard_interactive_checkout_resilience(page: Page, base_url: str):
    """Validate interactive resilience checkout execution and graceful fallback quote."""
    page.goto(f"{base_url}/dashboard", wait_until="networkidle")
    
    # Fill in customer details
    zip_select = page.locator("#checkout-zip")
    zip_select.select_option("90210")
    weight_input = page.locator("#checkout-weight")
    weight_input.fill("2.5")
    customer_input = page.locator("#checkout-customer")
    customer_input.fill("CUST-PLAYWRIGHT-TEST")
    
    # Submit transaction
    submit_btn = page.locator("#btn-submit-checkout")
    expect(submit_btn).to_be_enabled()
    submit_btn.click()
    
    # Wait for result box to open
    result_box = page.locator("#checkout-result-box")
    expect(result_box).to_be_visible(timeout=10000)
    
    # Check HTTP status badge
    http_badge = page.locator("#res-http-badge")
    expect(http_badge).to_contain_text("200 OK")
    
    # Check Status Title (Graceful Fallback Estimate)
    status_title = page.locator("#res-status-title")
    expect(status_title).to_have_text("CONFIRMED_ESTIMATED_SHIPPING")
    
    # Check Latency is within SLA budget (< 1500ms)
    latency_el = page.locator("#res-latency")
    expect(latency_el).to_contain_text("ms")
    
    # Check Fallback Alert Banner
    fallback_alert = page.locator("#fallback-alert")
    expect(fallback_alert).to_be_visible()
    rate_el = page.locator("#alert-fallback-rate")
    expect(rate_el).to_have_text(re.compile(r"^\$\d+\.\d{2}$"))
    
    # Open Raw JSON accordion and verify structured receipt
    page.locator("summary:has-text('View Full Raw Response Payload')").click()
    json_viewer = page.locator("#raw-json-viewer")
    expect(json_viewer).to_be_visible()
    json_text = json_viewer.inner_text()
    data = json.loads(json_text)
    assert data.get("status") == "CONFIRMED_ESTIMATED_SHIPPING"
    assert data.get("shipping_details", {}).get("is_fallback") is True

def test_web_dashboard_cryptographic_evidence_receipt_and_gates(page: Page, base_url: str):
    """Validate that the dashboard dynamically loads and displays the verified evidence receipt and 11 quality gates."""
    page.goto(f"{base_url}/dashboard", wait_until="networkidle")
    
    # Wait for dynamic hydration of evidence badge
    status_badge = page.locator("#evidence-receipt-status-badge")
    expect(status_badge).to_have_text("RECOVERED_AND_VERIFIED", timeout=10000)
    
    # Check Cryptographic Seal
    seal_el = page.locator("#evidence-seal-display")
    expect(seal_el).to_be_visible()
    seal_text = seal_el.inner_text()
    assert len(seal_text) >= 16
    assert not seal_text.startswith("loading")
    
    # Gate 1: Baseline SLA breach
    expect(page.locator("text=1. Baseline SLA Breach")).to_be_visible()
    expect(page.locator("text=3,742.46ms > 1,500ms budget recorded")).to_be_visible()
    
    # Gate 2: Deterministic bisect
    expect(page.locator("text=2. Deterministic Bisect")).to_be_visible()
    expect(page.locator("div:has-text('2. Deterministic Bisect')").first).to_contain_text("974035c")
    
    # Gate 3: Profile Hash Match
    expect(page.locator("#gate-hash-val")).to_have_text("644a89784316")
    
    # Gate 4: Consecutive Passes
    expect(page.locator("#gate-probes-val")).to_have_text("10 / 10")
    
    # Gate 5: Under SLA budget
    expect(page.locator("text=5. Under SLA Budget")).to_be_visible()
    
    # Gate 6: Latency Reduction
    expect(page.locator("text=6. >60% Latency Reduction")).to_be_visible()
    
    # Gate 7: Observable Fallback
    expect(page.locator("text=7. Observable Fallback")).to_be_visible()
    
    # Gate 8: Secret Scanning
    expect(page.locator("text=8. Secret Scanning")).to_be_visible()
    
    # Gate 9: Bandit AST SAST
    expect(page.locator("text=9. Bandit AST SAST")).to_be_visible()
    
    # Gate 10: Container Digest
    expect(page.locator("text=10. Container Digest")).to_be_visible()
    
    # Gate 11: Supervised Gate (Human sign-off required)
    gate11_val = page.locator("#gate-promotion-status-val")
    expect(gate11_val).to_be_visible()
    expect(gate11_val).to_contain_text("BLOCKED_PENDING_APPROVAL")
    
    # Anti-Fake Truth Audit
    expect(page.locator("text=Anti-Fake Truth Audit")).to_be_visible()

def test_web_dashboard_nine_lifecycle_stages(page: Page, base_url: str):
    """Validate that all 9 lifecycle stages are displayed and confirmed."""
    page.goto(f"{base_url}/dashboard", wait_until="networkidle")
    
    # Stages Count Badge
    badge = page.locator("#stages-count-badge")
    expect(badge).to_be_visible()
    expect(badge).to_have_text("9 / 9 STAGES COVERED")
    
    # Verify all 9 Stage cards exist
    expected_stages = [
        ("plan", "STAGE 1", "PLAN"),
        ("create", "STAGE 2", "CREATE"),
        ("configure", "STAGE 3", "CONFIGURE"),
        ("verify", "STAGE 4", "VERIFY"),
        ("secure", "STAGE 5", "SECURE"),
        ("package", "STAGE 6", "PACKAGE"),
        ("release", "STAGE 7", "RELEASE"),
        ("monitor", "STAGE 8", "MONITOR"),
        ("govern", "STAGE 9", "GOVERN"),
    ]
    
    for stage_id, stage_num, stage_name in expected_stages:
        card = page.locator(f"#stage-card-{stage_id}")
        expect(card).to_be_visible()
        expect(card).to_contain_text(stage_num)
        expect(card).to_contain_text(stage_name)

def test_web_openapi_swagger_documentation(page: Page, base_url: str):
    """Validate that the interactive Swagger OpenAPI docs render properly."""
    page.goto(f"{base_url}/docs", wait_until="networkidle")
    expect(page).to_have_title(re.compile("Swagger UI", re.IGNORECASE))
    
    # Check header and API routes in Swagger UI
    expect(page.locator(".title:has-text('FaultForge Checkout Service')")).to_be_visible()
    expect(page.locator("span:has-text('/health')").first).to_be_visible()
    expect(page.locator("span:has-text('/api/v1/checkout')").first).to_be_visible()
    expect(page.locator("span:has-text('/api/v1/evidence')").first).to_be_visible()
    expect(page.locator("span:has-text('/api/v1/ledger')").first).to_be_visible()

def test_direct_api_backend_consistency(page: Page, base_url: str):
    """Directly validate JSON schema contracts for evidence and ledger via Playwright APIRequestContext."""
    # 1. Health check
    res_health = page.request.get(f"{base_url}/health")
    assert res_health.status == 200
    h_data = res_health.json()
    assert h_data.get("status") == "healthy"
    assert "revision" in h_data
    
    # 2. Evidence Receipt Contract
    res_ev = page.request.get(f"{base_url}/api/v1/evidence")
    assert res_ev.status == 200
    ev_data = res_ev.json()
    assert ev_data.get("final_status") == "RECOVERED_AND_VERIFIED"
    assert ev_data.get("governance", {}).get("promotion_gate") == "BLOCKED_PENDING_APPROVAL"
    assert ev_data.get("fault_profile", {}).get("hash") == "644a89784316"
    assert ev_data.get("fault_profile", {}).get("identical_replay_confirmed") is True
    assert ev_data.get("duo_execution", {}).get("status") == "CONFIRMED"
    assert len(ev_data.get("run_history_15_probes", [])) == 15
    assert ev_data.get("not_established") == []
    assert len(ev_data.get("tamper_evident_seal_sha256", "")) == 64
    
    # 3. 9-Stage Ledger Contract
    res_led = page.request.get(f"{base_url}/api/v1/ledger")
    assert res_led.status == 200
    led_data = res_led.json()
    stages = led_data.get("stages", {})
    assert len(stages) == 9
    for expected in ["plan", "create", "configure", "verify", "secure", "package", "release", "monitor", "govern"]:
        assert expected in stages
        assert stages[expected].get("status") == "SUCCESS"
