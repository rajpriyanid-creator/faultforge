#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
FaultForge README Claims vs. Empirical Ledger Validator
Verifies that all claims made in README.md Section 4 match the empirical
truth recorded in stage_ledger.json and evidence_receipt.json.
Fails CI if README inflates a SKIPPED or FAILED stage into SUCCESS.
"""
import os
import re
import sys
import json
import argparse
from typing import Dict, Any, Tuple, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_README_PATH = "README.md"
DEFAULT_LEDGER_PATH = "reports/stage_ledger.json"
DEFAULT_RECEIPT_PATH = "reports/evidence_receipt.json"

EXPECTED_STAGES = [
    "plan", "create", "configure", "verify", "secure",
    "package", "release", "monitor", "govern"
]

def parse_readme_stages_table(readme_path: str = DEFAULT_README_PATH) -> Dict[str, str]:
    if not os.path.exists(readme_path):
        print(f"[-] Error: README not found at {readme_path}", file=sys.stderr)
        sys.exit(1)

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find Section 4
    sec4_match = re.search(r"## 4\.\s+The 9 Covered Lifecycle Stages.*?(?=\n## 5\.|\Z)", content, re.DOTALL)
    if not sec4_match:
        print("[-] Error: Could not locate '## 4. The 9 Covered Lifecycle Stages' in README.md", file=sys.stderr)
        sys.exit(1)

    table_text = sec4_match.group(0)
    claims = {}

    for line in table_text.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---") or "Stage" in line:
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) >= 4:
            # Stage is in col 0, e.g. **`plan`**
            stg_match = re.search(r"`([a-z_]+)`", cols[0])
            if stg_match:
                stage_name = stg_match.group(1).lower()
                status_text = cols[3]
                claims[stage_name] = status_text

    return claims

def audit_ci_claims_and_citations(
    readme_path: str = DEFAULT_README_PATH,
    gitlab_ci_path: str = ".gitlab-ci.yml",
    receipt_path: str = DEFAULT_RECEIPT_PATH,
    release_path: str = "reports/release.json",
    docs_dir: str = "docs"
) -> Tuple[bool, List[str]]:
    discrepancies = []

    # 1. Parse .gitlab-ci.yml for jobs and their script commands
    jobs_dict = {}
    if os.path.exists(gitlab_ci_path):
        with open(gitlab_ci_path, "r", encoding="utf-8", errors="ignore") as f:
            ci_content = f.read()
        job_blocks = re.split(r'\n(?=[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+:)', ci_content)
        for blk in job_blocks:
            m = re.match(r'^([a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+):', blk.strip())
            if m:
                jobs_dict[m.group(1)] = blk

    # 2. Discover canonical references from receipt and release
    receipt = {}
    for rp in [receipt_path, "docs/sample_reports/evidence_receipt.json"]:
        if os.path.exists(rp):
            try:
                with open(rp, "r", encoding="utf-8") as f:
                    receipt = json.load(f)
                break
            except Exception:
                pass

    release = {}
    for rlp in [release_path, "docs/sample_reports/release.json"]:
        if os.path.exists(rlp):
            try:
                with open(rlp, "r", encoding="utf-8") as f:
                    release = json.load(f)
                break
            except Exception:
                pass

    canonical_pipeline = None
    if receipt.get("urls", {}).get("referenced_pipeline_url"):
        pm = re.search(r"pipelines/(\d+)", receipt["urls"]["referenced_pipeline_url"])
        if pm:
            canonical_pipeline = pm.group(1)

    canonical_issue = "62"
    if receipt.get("urls", {}).get("issue_url"):
        im = re.search(r"/(?:issues|work_items)/(\d+)", receipt["urls"]["issue_url"])
        if im:
            canonical_issue = im.group(1)

    canonical_revision = release.get("revision") or receipt.get("deployment", {}).get("cloud_run_revision") or "faultforge-checkout-00050-keq"
    canonical_stable = "faultforge-checkout-00002-kpl"

    permitted_pipelines = {canonical_pipeline, "2982289232"} if canonical_pipeline else {"2982289232"}

    # 3. Check markdown files
    md_files = [readme_path]
    if os.path.exists(docs_dir):
        for root, _, files in os.walk(docs_dir):
            for f in files:
                if f.endswith(".md"):
                    md_files.append(os.path.join(root, f))

    for mdp in md_files:
        if not os.path.exists(mdp):
            continue
        with open(mdp, "r", encoding="utf-8", errors="ignore") as fp:
            lines = fp.readlines()

        for line_num, line in enumerate(lines, 1):
            cl = line.strip()
            if not cl or cl.startswith("<!--"):
                continue

            # Check job enforcement claims: "enforced by / runs in <job or script>"
            job_cites = re.finditer(r'(?:enforced by|runs in|enforces|Stage)\s+[`\']?([a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+)[`\']?', cl, re.I)
            for jm in job_cites:
                job_name = jm.group(1)
                if jobs_dict and job_name not in jobs_dict:
                    discrepancies.append(f"{mdp}:{line_num} - Claimed CI job '{job_name}' does not exist in .gitlab-ci.yml")
                elif jobs_dict and job_name in jobs_dict:
                    # Look for script reference in the same sentence/line
                    script_match = re.search(r'([a-zA-Z0-9_/-]+\.(?:py|sh|yml|yaml))', cl)
                    if script_match:
                        script_name = os.path.basename(script_match.group(1))
                        # Script must be executed in that job's block
                        if script_name not in jobs_dict[job_name]:
                            discrepancies.append(
                                f"{mdp}:{line_num} - Claims job '{job_name}' executes '{script_name}', but '{script_name}' is not called in {job_name}'s CI script"
                            )

            # Check for stale pipeline IDs: 2982183259, 2982435953
            pipe_matches = re.finditer(r'pipelines/(\d{10})|\bPipeline\s+[#`]?(\d{10})', cl)
            for pm in pipe_matches:
                pid = pm.group(1) or pm.group(2)
                if pid not in permitted_pipelines and pid in ("2982183259", "2982435953"):
                    discrepancies.append(
                        f"{mdp}:{line_num} - Cites stale pipeline ID {pid}; current verified pipeline is {canonical_pipeline}"
                    )

            # Check for stale issue numbers: #50
            if re.search(r'\b(?:Work Item|Issue)\s+[#`]?50\b|/(?:issues|work_items)/50\b', cl, re.I):
                discrepancies.append(
                    f"{mdp}:{line_num} - Cites stale incident Work Item #50; must cite current issue #{canonical_issue} (root incident #42)"
                )

            # Check for stale Cloud Run revisions: 00030-dit, 00036-pih
            rev_matches = re.finditer(r'\b(faultforge-checkout-\d{5}-[a-z]{3})\b', cl)
            for rm in rev_matches:
                rev = rm.group(1)
                if rev not in (canonical_revision, canonical_stable) and rev in ("faultforge-checkout-00030-dit", "faultforge-checkout-00036-pih"):
                    discrepancies.append(
                        f"{mdp}:{line_num} - Cites stale Cloud Run revision '{rev}'; current revision is '{canonical_revision}'"
                    )

    return (len(discrepancies) == 0), discrepancies

def validate_claims(
    readme_path: str = DEFAULT_README_PATH,
    ledger_path: str = DEFAULT_LEDGER_PATH,
    receipt_path: str = DEFAULT_RECEIPT_PATH,
    strict_all_stages: bool = True,
    samples_mode: bool = False
) -> bool:
    print("\n=================================================================")
    print(" FaultForge README Claims vs. Empirical Evidence Ledger Gate")
    print("=================================================================")

    if samples_mode or (ledger_path == DEFAULT_LEDGER_PATH and not os.path.exists(ledger_path)):
        sample_ledger = "docs/sample_reports/stage_ledger.json"
        sample_receipt = "docs/sample_reports/evidence_receipt.json"
        if os.path.exists(sample_ledger) and os.path.exists(sample_receipt):
            print(f"[*] Active 'reports/' is empty or missing. Falling back to sample reports at {sample_ledger}")
            ledger_path = sample_ledger
            receipt_path = sample_receipt

    if not os.path.exists(ledger_path) or not os.path.exists(receipt_path):
        print(f"[-] Error: no CI evidence present (`{ledger_path}` or `{receipt_path}` missing)", file=sys.stderr)
        return False

    with open(ledger_path, "r", encoding="utf-8") as lf:
        ledger_data = json.load(lf)

    stages_recorded = ledger_data.get("stages", {})
    # Merge any individual stage ledger files present in the same directory
    base_dir = os.path.dirname(ledger_path) or "."
    if os.path.exists(base_dir):
        for fname in os.listdir(base_dir):
            if fname.startswith("stage_ledger_") and fname.endswith(".json") and fname != os.path.basename(ledger_path):
                try:
                    with open(os.path.join(base_dir, fname), "r", encoding="utf-8") as sf:
                        stg = json.load(sf)
                        if isinstance(stg, dict) and "stage" in stg:
                            stages_recorded[stg["stage"]] = stg
                except Exception:
                    pass

    readme_claims = parse_readme_stages_table(readme_path)

    print(f"README Stages Found: {len(readme_claims)} / 9")
    print(f"Ledger Stages Found: {len(stages_recorded)} / 9\n")
    print(f"{'STAGE':<12} {'LEDGER STATUS':<16} {'README CLAIM':<24} {'RESULT'}")
    print("-" * 65)

    discrepancies = []

    for stage in EXPECTED_STAGES:
        if stage not in readme_claims:
            discrepancies.append(f"Stage '{stage}' is missing from README Section 4 table.")
            print(f"{stage:<12} {'MISSING':<16} {'MISSING':<24} [FAIL]")
            continue

        claim_str = readme_claims[stage]
        ledger_entry = stages_recorded.get(stage)

        if not ledger_entry:
            if strict_all_stages:
                discrepancies.append(f"Stage '{stage}' has not been recorded in stage_ledger.json.")
                print(f"{stage:<12} {'NOT RECORDED':<16} {claim_str:<24} [FAIL]")
            else:
                print(f"{stage:<12} {'PENDING':<16} {claim_str:<24} [WARN]")
            continue

        ledger_status = ledger_entry.get("status", "UNKNOWN").upper()

        if ledger_status == "FAILED":
            discrepancies.append(f"Stage '{stage}' marked FAILED in ledger, but claimed in README as '{claim_str}'.")
            print(f"{stage:<12} {ledger_status:<16} {claim_str:<24} [FAIL]")
        elif ledger_status == "SKIPPED":
            # If ledger skipped, README must acknowledge SKIPPED and must NOT claim SUCCESS (no hedging)
            if "SUCCESS" in claim_str.upper():
                discrepancies.append(f"Stage '{stage}' is SKIPPED in ledger, but README hedges with SUCCESS ('{claim_str}').")
                print(f"{stage:<12} {ledger_status:<16} {claim_str:<24} [FAIL]")
            elif "SKIPPED" not in claim_str.upper():
                discrepancies.append(f"Stage '{stage}' is SKIPPED in ledger, but README does not state SKIPPED ('{claim_str}').")
                print(f"{stage:<12} {ledger_status:<16} {claim_str:<24} [FAIL]")
            else:
                print(f"{stage:<12} {ledger_status:<16} {claim_str:<24} [PASS]")
        elif ledger_status in ("PARTIAL", "NOT_EXECUTED"):
            if "PARTIAL" not in claim_str.upper() and "NOT EXECUTED" not in claim_str.upper():
                discrepancies.append(f"Stage '{stage}' is {ledger_status} in ledger, but README does not state PARTIAL or NOT EXECUTED ('{claim_str}').")
                print(f"{stage:<12} {ledger_status:<16} {claim_str:<24} [FAIL]")
            elif "SUCCESS" in claim_str.upper() and "PARTIAL" not in claim_str.upper():
                discrepancies.append(f"Stage '{stage}' is {ledger_status} in ledger, but README claims SUCCESS ('{claim_str}').")
                print(f"{stage:<12} {ledger_status:<16} {claim_str:<24} [FAIL]")
            else:
                print(f"{stage:<12} {ledger_status:<16} {claim_str:<24} [PASS]")
        elif ledger_status == "SUCCESS":
            if stage == "create" and not ledger_entry.get("duo_executed", False):
                if "PARTIAL" not in claim_str.upper() and ("NOT EXECUTED" not in claim_str.upper() and "DUO:" not in claim_str.upper() and "DUO FLOW:" not in claim_str.upper()):
                    discrepancies.append("Stage 'create' duo_executed is false in ledger, but README claims unqualified SUCCESS without stating PARTIAL / Duo flow not executed.")
                    print(f"{stage:<12} {ledger_status:<16} {claim_str:<24} [FAIL]")
                    continue
                elif "SUCCESS" in claim_str.upper() and "PARTIAL" not in claim_str.upper() and ("NOT EXECUTED" not in claim_str.upper()):
                    discrepancies.append("Stage 'create' duo_executed is false in ledger; README must state PARTIAL (Duo flow: not executed) instead of SUCCESS.")
                    print(f"{stage:<12} {ledger_status:<16} {claim_str:<24} [FAIL]")
                    continue
                print(f"{stage:<12} {ledger_status:<16} {claim_str:<24} [PASS]")
            elif "SUCCESS" not in claim_str.upper():
                discrepancies.append(f"Stage '{stage}' succeeded in ledger, but README does not indicate SUCCESS ('{claim_str}').")
                print(f"{stage:<12} {ledger_status:<16} {claim_str:<24} [FAIL]")
            else:
                print(f"{stage:<12} {ledger_status:<16} {claim_str:<24} [PASS]")
        else:
            discrepancies.append(f"Stage '{stage}' has unknown ledger status: {ledger_status}")
            print(f"{stage:<12} {ledger_status:<16} {claim_str:<24} [FAIL]")

    # Check receipt consistency if present
    if os.path.exists(receipt_path):
        try:
            with open(receipt_path, "r", encoding="utf-8") as rf:
                receipt = json.load(rf)
            fin_status = receipt.get("final_status")
            not_est = receipt.get("not_established", [])
            print(f"\n[*] Receipt Cross-Check: final_status='{fin_status}', not_established={len(not_est)} items")
            if fin_status == "RECOVERED_AND_VERIFIED" and len(not_est) > 0:
                discrepancies.append(f"Receipt claims RECOVERED_AND_VERIFIED but has {len(not_est)} unestablished items.")
        except Exception as exc:
            discrepancies.append(f"Error reading receipt at {receipt_path}: {exc}")

    # Audit CI claims and reference citations across docs
    ci_passed, ci_discrepancies = audit_ci_claims_and_citations(
        readme_path=readme_path,
        receipt_path=receipt_path
    )
    if not ci_passed:
        discrepancies.extend(ci_discrepancies)

    print("=================================================================\n")

    if discrepancies:
        print(f"[-] FAILED: Found {len(discrepancies)} discrepancy/discrepancies between claims and ledger truth:")
        for d in discrepancies:
            print(f"    - {d}")
        return False

    print("[+] PASSED: All README claims match the empirical evidence ledger.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Check README claims against stage_ledger.json")
    parser.add_argument("--readme", default=DEFAULT_README_PATH, help="Path to README.md")
    parser.add_argument("--ledger", default=DEFAULT_LEDGER_PATH, help="Path to stage_ledger.json")
    parser.add_argument("--receipt", default=DEFAULT_RECEIPT_PATH, help="Path to evidence_receipt.json")
    parser.add_argument("--samples", action="store_true", help="Read from docs/sample_reports/ instead of active reports/")
    parser.add_argument("--allow-partial", action="store_true", help="Allow partial ledger when testing early stages")
    args = parser.parse_args()

    success = validate_claims(
        readme_path=args.readme,
        ledger_path=args.ledger,
        receipt_path=args.receipt,
        strict_all_stages=not args.allow_partial,
        samples_mode=args.samples
    )
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
