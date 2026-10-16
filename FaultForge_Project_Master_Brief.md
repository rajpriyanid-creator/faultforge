# FaultForge — Break It, Heal It
## Project Master Brief for GitLab Transcend 2026: Life After Code

**Document purpose:** A single source of truth for the project idea, product scope, architecture, workflow, technical decisions, safety rules, validation criteria, and hackathon prize strategy.

**Prepared:** 15 October 2026  
**Working project name:** **FaultForge**  
**Internal concept name:** **Break It, Heal It**  
**Tagline:** *Rehearse a failure. Recover safely. Prove the service is stronger.*

> **One-sentence pitch:** FaultForge uses GitLab Duo Agent Platform to inject a controlled dependency failure into an isolated application environment, diagnose the code or configuration weakness that makes the application fail, recover safely, open a resilience-hardening merge request, and prove the fix by replaying the same fault.

---

## 1. Executive Summary

FaultForge is an AI-assisted software reliability system focused on **controlled chaos testing, evidence-backed diagnosis, safe recovery, and verified resilience improvements**.

Most basic CI pipelines tell a developer that a test failed. Many AI coding agents can suggest a patch. FaultForge connects those actions into a controlled engineering workflow:

1. Introduce a repeatable network fault in a disposable test/staging environment.
2. Detect and record the resulting failure.
3. Collect concise evidence from the test, logs, Git history, and GitLab records.
4. Identify the most likely regression or weakness without pretending that every fault has a guilty commit.
5. Contain the failure or keep the candidate release from receiving traffic.
6. Use GitLab Duo Agent Platform to propose a minimal resilience fix and open a merge request.
7. Run the normal tests and a new regression test.
8. Replay the exact same fault configuration against the patched version.
9. Promote only after independent checks pass; otherwise keep or restore the stable version.
10. Attach a clear record of what was tested, what changed, what passed, and what remains uncertain.

**The differentiator is not “AI says it fixed the app.” It is the before/after proof under the same controlled failure condition.**

The recommended first implementation is one MIT-licensed FastAPI or Express service, one downstream dependency, one primary fault, one GitLab Duo custom flow, and one complete verified recovery/hardening loop. Additional faults and lifecycle stages come only after that loop works reliably.

---

## 2. Essential Hackathon Context

Official event: [GitLab Transcend — Life After Code](https://gitlab-transcend.devpost.com/?ref_medium=discover)  
Resources: [Official hackathon resources](https://gitlab-transcend.devpost.com/resources)  
Rules: [Official rules page](https://gitlab-transcend.devpost.com/rules)

### Event constraints relevant to FaultForge

- **Deadline:** 27 October 2026 at 1:00 PM UTC, which is **6:30 PM India Standard Time**. Verify the event page and announcements in case organizers update anything.
- **Total prize pool:** $45,000.
- **Required platform:** The project must meaningfully use GitLab Duo Agent Platform capabilities, such as agents, flows, triggers, or MCP integrations. A chatbot or dashboard alone is not enough.
- **Path A — Start Fresh:** New project, CI/CD, and post-code automation created for the hackathon; deployment is optional.
- **Path B — Bring Your Own:** Start from an existing MIT-licensed open-source project (your own project or a fork), import it to GitLab, build the new agentic automation and deployment during the permitted submission period, and provide a public deployed URL. The current instructions specify that the automation and deployment must be new work completed on or after 5 October 2026; the deployed project should stay live until winners are announced, around 16 November 2026.
- **Google Cloud bonus:** Up to **+0.2 points** if the project is deployed on Google Cloud, deployment code is included in the public GitLab repository, and the live link is provided.
- **One official autonomy level must be selected:** Assisted, Supervised, or Hands-off. Do not present the same submission as simultaneously entering all three autonomy prizes.
- **The nine lifecycle stages:** `plan`, `create`, `verify`, `package`, `secure`, `release`, `configure`, `monitor`, `govern`. Only count a stage when the project performs real work in it; do not create empty jobs purely to claim coverage.

### Relevant judging dimensions

The current event lists:

1. **Technological Implementation** — real, non-trivial GitLab automation and working implementation.
2. **Design** — a coherent end-to-end workflow, not a disconnected proof of concept.
3. **Potential Impact** — a credible, useful solution to a real problem.
4. **Innovation / Idea** — meaningful differentiation from existing concepts.
5. **Presentation** — how clearly the project communicates its value and working behavior.

This project should primarily optimize for reliable engineering, a complete workflow, specific impact, and provable differentiation.

### Prize categories that matter most to FaultForge

| Prize category | Published prize | Fit and focus |
|---|---:|---|
| **Path B — Best Supervised Agent** | **$4,000** | **Primary target.** The agent carries out diagnosis, repair preparation, testing, and staging checks; a human approves the final promotion or high-risk action. This matches the intended safety design. |
| **Path B — Most Stages Covered** | **$5,000** | **Secondary target.** Implement several real lifecycle stages end-to-end: incident/work-item creation, code change, verification, packaging, security checks, release/configuration, monitoring, and governance. |
| **Most Creative** | **$4,000** | **Additional opportunity.** The distinct idea is to create a controlled fault, recover, harden the code, and verify the hardening against the same fault. |
| Google Cloud deployment bonus | **Up to +0.2 points** | Worth pursuing if Cloud Run deployment is reliable and the required public code/live link can be supplied. |
| Most Environmentally Impactful | **$5,000** | **Not a core target.** Only consider this later if the project has time to measure genuine sustainability improvements using an appropriate public methodology such as the Software Carbon Intensity (SCI) framework. Do not invent carbon savings. |

Awards and bonus points are not guaranteed. Do not assume separate prizes can always be stacked; follow the current submission form and official rules.

**Why Supervised rather than Hands-off:** FaultForge includes a risk gate and requires human approval before high-impact production promotion. That behavior naturally fits Supervised. Hands-off is a $5,000 category, but it implies a complete workflow without an intermediate human. Do not claim Hands-off while relying on human approval as part of the normal workflow.

---

## 3. Product Identity and Scope

### Product name

**FaultForge**

### Descriptive subtitle

**Chaos Rehearsal, Verified Recovery & Resilience Hardening for GitLab**

“Break It, Heal It” describes the workflow in plain language and can be used as the internal concept name or product tagline.

### Target users

- Backend engineers responsible for services that call external APIs or databases.
- Platform engineering and DevOps teams responsible for CI/CD and releases.
- Site reliability engineers (SREs) who investigate incidents and recovery.
- Teams that want to validate whether a release can tolerate dependency failures before trusting it.

### Primary problem

A service can pass ordinary unit tests and still fail when an external dependency slows down, resets connections, or becomes intermittently unavailable. Unit tests often mock the dependency and therefore never exercise the real timeout, retry, or fallback behavior. When the problem appears after deployment, engineers must correlate logs, recent changes, release versions, and infrastructure state manually.

FaultForge tests that weakness under controlled conditions and connects diagnosis to a verified code-level improvement.

### Product promise

FaultForge should be able to answer the following with evidence:

- What fault was injected?
- What observable failure did it cause?
- Which recent code/configuration change may have made the service fragile?
- Is the diagnosis confirmed by a reproducible test, or only a hypothesis?
- What recovery action was taken?
- What code change was proposed?
- Did the normal test suite and security checks pass?
- Did the exact same fault stop causing the original failure?
- Was the release promoted, kept isolated, or rolled back?
- What remains uncertain or requires human review?

### Explicit non-goals

FaultForge is **not** intended to be:

- A general-purpose chatbot for DevOps questions.
- A generic issue-to-production agent that claims to automate everything.
- An unrestricted agent operating directly on production systems.
- A tool that automatically rewrites arbitrary application code after any alert.
- A replacement for deterministic tests, health checks, monitoring, security scans, or approval policies.
- A multi-repository migration platform.
- A database-migration automation platform.
- A full chaos-engineering platform supporting dozens of fault types at launch.
- A sustainability dashboard as its primary product.
- A system that labels a change as the confirmed cause merely because it occurred near the incident.

Keep the product narrow and make the core workflow real.

---

## 4. The Core User Story

> As a developer, I want to know whether my service survives realistic dependency failures, and if it does not, I want the system to help diagnose the weakness, prepare a safe fix, and prove the fix works before release.

### Example scenario

A checkout service calls a shipping-rate API. The call has no sufficiently strict timeout and no graceful fallback. The unit test suite passes because the shipping API is mocked.

FaultForge routes that dependency through Toxiproxy in an isolated test environment and adds a controlled 3–4 second delay. The checkout request now times out or returns a 5xx response.

The system saves the failure evidence, checks the relevant code and recent merge requests, and identifies an unbounded outbound request as the likely weakness. If a known bad commit has been planted and the same chaos test can distinguish good and bad revisions, a deterministic `git bisect` can identify the regression. The Duo agent then proposes a bounded timeout, limited retry/backoff where appropriate, a graceful fallback, and a regression test.

The candidate patch is not accepted just because the agent says it is correct. The pipeline re-runs the same fault profile against the patched code. The fix is considered verified only when explicit test and health criteria pass.

**Important distinction:** Toxiproxy creates the test condition; it does not inherently identify a guilty commit. `git bisect` is justified only if the failure reproduces differently across revisions because a code/configuration change introduced or removed the relevant resilience behavior. If the fault itself is the only cause, the system must report that fact rather than inventing a guilty commit.

---

## 5. End-to-End Workflow

The intended workflow is one coordinated GitLab Duo custom flow with deterministic CI scripts and a small number of agent responsibilities.

### Stage 0 — Establish a trusted baseline

- Build and run the selected service.
- Record the current commit and deployment revision.
- Confirm the ordinary health check and normal test suite pass.
- Record baseline latency and error rate under normal conditions.
- Keep the last known-good revision identifiable.
- Ensure the fault is isolated to the test/staging environment.

### Stage 1 — Inject a controlled fault

Use Toxiproxy to simulate one primary fault in the service's outbound dependency path.

The initial scenario should be **a slow downstream HTTP dependency**. A delay of roughly 3–4 seconds is a test configuration, not a guaranteed performance result.

The fault profile must be deterministic and recorded, including toxic type, latency/jitter values, target proxy, test run ID, and configuration hash or equivalent identifier.

### Stage 2 — Detect and capture the failure

A deterministic health/probe job records:

- HTTP status codes and request outcomes.
- Response latency, including p95/p99 when sufficient samples exist.
- Error counts and the relevant failed assertion.
- A bounded excerpt of application and dependency logs.
- Commit SHA, pipeline URL, test run ID, and the injected fault configuration.
- Current candidate and known-good deployment revisions where applicable.

The job should fail for a clearly defined reason. “The AI thinks the service looks unhealthy” is not a valid trigger.

### Stage 3 — Build a compact incident dossier

A script filters and normalizes the evidence before sending context to a Duo flow. Send the minimum useful evidence; do not submit thousands of lines of raw logs.

The dossier should include:

- Incident/run identifier.
- Repository and commit identifiers.
- Failed test and probe output.
- Exact fault configuration.
- Relevant stack trace/log excerpt.
- Recent commits or merge requests that touched the affected code path.
- Current and stable revisions, if available.
- Links to pipeline jobs and source files.
- Which facts are confirmed versus inferred.

Secrets, tokens, personal data, and unnecessary log content must be removed.

### Stage 4 — Diagnose the weakness

The Diagnostician uses evidence to find the relevant outbound call, configuration, or code path.

Preferred evidence order:

1. Directly reproducible failing test or probe.
2. Source code at the failing call site.
3. Diff of recent changes touching that call site.
4. Git history and relevant merge requests.
5. Orbit graph context if it is enabled and useful.
6. A ranked hypothesis only where the evidence cannot confirm a single cause.

Use deterministic processing for log filtering, health checks, change-range inspection, and a reproducible bisect. Use the AI agent for contextual reasoning and a repair plan.

The result must distinguish **confirmed regression**, **likely cause**, and **insufficient evidence**. A false certainty is worse than a clear request for additional evidence.

### Stage 5 — Contain or prevent unsafe promotion

The first protection is that a failing candidate must not be promoted.

- For a CI fault-replay failure, fail the release gate and preserve the stable version.
- If a canary revision is actually receiving traffic and independent health checks show a failure, use the approved rollback mechanism to route traffic to the known-good revision.
- Verify the service again after rollback. Changing traffic routing by itself is not proof that external dependencies or health have recovered.
- Create or update a GitLab issue/work item with the incident details and links to the evidence.

Do not run chaos experiments against an uncontrolled production service.

### Stage 6 — Create a remediation merge request

The Healer/Hardener logic proposes the smallest relevant change, such as:

- A bounded connect/read timeout.
- Limited retries with exponential backoff and jitter for safe, idempotent requests.
- A circuit breaker or bulkhead where justified.
- A graceful fallback response that is observable and does not silently misrepresent data.
- A regression test that reproduces the original failure.

Do not add retries blindly. Retrying non-idempotent payment, checkout, or mutation requests can duplicate side effects. Keep the MVP scenario on a safe, idempotent dependency call such as a shipping-rate lookup.

The agent should open a merge request with explanation, risk classification, test evidence, and rollback considerations. It must not push unreviewed changes directly into a protected main branch.

### Stage 7 — Verify the patch

The CI pipeline must run:

- Formatting/linting and unit tests.
- The original baseline tests.
- The new regression test.
- The exact same Toxiproxy fault configuration.
- Health/latency checks with predefined pass/fail thresholds.
- Relevant GitLab security checks such as SAST and secret detection, where available.
- Any required packaging checks.

The fault profile must match the baseline experiment. If the fault is weaker or the test inputs differ, a green result is not valid proof of remediation.

### Stage 8 — Controlled release

After the candidate passes the required gates:

- Build the container image.
- Deploy the candidate to a non-production Cloud Run revision or staging environment.
- Run post-deployment smoke/health checks.
- Promote the candidate only according to the selected Supervised policy.
- If the checks fail, keep or restore the stable revision and report the failure.

Cloud Run supports versioned revisions and traffic rollback. Use the official [Cloud Run rollback and traffic migration instructions](https://docs.cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration).

### Stage 9 — Final proof and audit record

Attach an incident/recovery report to the issue and/or merge request containing:

- Fault type and exact configuration.
- Before/after error counts and latency statistics.
- Diagnosis confidence and evidence links.
- Recovery action and outcome.
- Patch/MR commit identifiers.
- Unit, regression, chaos-replay, and security test results.
- Stable/candidate deployment identifiers, if applicable.
- Risk-policy decision and any human approval.
- Final status: `RECOVERED_AND_VERIFIED`, `CONTAINED_NEEDS_REVIEW`, or `NOT_VERIFIED`.
- Anything the system could not establish.

The report should be generated from actual job results. Never fabricate timings, pass rates, rollback duration, or “zero error” claims.

---

## 6. Fault Scenarios

### Mandatory primary scenario: Cascading hang from a slow dependency

**Setup:** A checkout/shipping endpoint makes an outbound request without a strict enough timeout. The request is routed through Toxiproxy during the test.

**Injected fault:** Add a controlled 3–4 second latency with optional jitter to the outbound dependency path.

**Expected baseline behavior:** The application exceeds its response budget, blocks too long, or returns an error. The failure must be reproducible in the test harness.

**Expected hardening:** Use a bounded timeout and controlled fallback. Add limited retry/backoff only if retries are appropriate for this operation. A circuit breaker may be added if it is genuinely needed and time permits.

**Proof:** Replay the identical latency fault and input against the hardened candidate. Show the original failing assertion now passes, the latency stays within the declared budget, and the fallback/response status is correct.

### Optional second scenario: Transient connection reset or 503 burst

Only implement after the first scenario is reliable.

**Injected fault:** Toxiproxy `reset_peer`, or a controlled transient 503 response from a downstream stub.

**Expected weakness:** Retry storm, unhandled connection error, or repeated request failures.

**Potential hardening:** Bounded retry with jitter, idempotency protection, connection-pool bounds, and appropriate fallback.

Do not add this scenario merely to enlarge the feature list. It must use a real test and a different failure mode.

### Toxiproxy notes

Toxiproxy is a TCP proxy designed for simulating network conditions. Its documented toxics include latency, bandwidth limits, connection reset, timeout, and packet loss.

Official reference: [Shopify Toxiproxy](https://github.com/Shopify/toxiproxy)

For the MVP, run the application, dependency stub, and Toxiproxy together in a GitLab CI/Docker Compose test network. This is easier to reproduce than immediately depending on a complex cloud sidecar topology.

---

## 7. The Crucial Diagnosis Rule: Do Not Misuse `git bisect`

The original idea combined chaos injection with culprit detection. That combination only makes sense when the test distinguishes revisions.

- **Chaos injection** introduces a controlled stress condition.
- **Regression diagnosis** identifies a code/configuration change that made the service fail under that condition.
- **`git bisect`** finds a regression boundary only when the same automated probe passes on good revisions and fails on bad revisions.

Example:

1. Earlier commit uses a timeout and passes the scripted latency probe.
2. A later commit removes the timeout or introduces an unbounded request.
3. The same Toxiproxy configuration makes the later version fail and earlier version pass.
4. `git bisect run` can use that deterministic probe to find the first failing revision.

If every revision fails under a fault because the test environment is configured incorrectly, `git bisect` cannot identify a meaningful code regression. If logs and diffs only suggest a cause, state that it is a hypothesis.

**Never make the AI invent a commit SHA or claim a root cause without supporting evidence.**

---

## 8. Recommended Architecture

### High-level flow

```text
GitLab repository / candidate merge request
                  |
                  v
        GitLab CI/CD pipeline
                  |
       baseline tests + health probe
                  |
                  v
          Toxiproxy fault test
                  |
       deterministic failure evidence
                  |
                  v
       compact incident dossier
                  |
                  v
    GitLab Duo custom flow / orchestrator
        /            |             \
       v             v              v
 Diagnostician     Healer         Hardener
       |             |              |
       +-------------+--------------+
                     |
             remediation MR
                     |
                     v
         tests + exact-fault replay
                     |
             +-------+-------+
             |               |
         checks pass      checks fail
             |               |
             v               v
    staging/Cloud Run   keep stable, stop
    verification       promotion, report
             |
             v
    Supervised promotion
             |
             v
       evidence receipt
```

### Important deployment boundary

Keep deterministic fault injection and replay in CI first. Cloud Run provides the public deployed application and, if implemented, controlled revision/canary promotion and rollback. Do not assume Toxiproxy must run as a Cloud Run sidecar for the core proof. That adds networking and deployment risk and is not necessary to prove a reproducible CI hardening loop.

If time and integration access permit, extend the same controlled fault path into a dedicated Cloud Run staging/canary setup. Do not connect fault injection to real production customer traffic.

---

## 9. Components and Agent Responsibilities

Build one coordinated custom flow. Three focused agent responsibilities are enough; do not create a large agent hierarchy simply for appearance.

### A. Orchestrator / Custom Flow

Responsibilities:

- Receive a structured incident dossier.
- Sequence investigation, remediation, validation, and reporting.
- Track state and halt on missing evidence or policy violations.
- Start or coordinate the appropriate CI checks and GitLab API actions.
- Never consider a change complete solely because an agent returned a success message.

### B. Diagnostician / Culprit

Responsibilities:

- Read the compact evidence dossier.
- Identify the outbound call, timeout/retry behavior, and relevant source files.
- Inspect relevant commits and merge requests using GitLab APIs.
- Use Orbit for relationship/context queries only if available and useful.
- Run or consume deterministic `git bisect` results only when the test supports revision comparison.
- Report evidence, confidence, and remaining unknowns.

### C. Healer

Responsibilities:

- Propose a minimal, scoped code/configuration patch.
- Prefer simple bounded timeouts and safe error handling over a broad rewrite.
- Follow repository conventions in `AGENTS.md`.
- Open a branch and merge request instead of directly changing protected branches.
- Explain intended behavior and risks.

### D. Hardener / Verification Planner

Responsibilities:

- Add a regression test for the original failure.
- Choose the same fault profile for the replay.
- Require successful unit, regression, and fault-injection tests.
- Confirm that the outcome improves without hiding errors or creating unsafe retries.
- Produce a human-readable report of actual test results.

The Healer and Hardener can be separate agents or separate flow components depending on how much the platform configuration supports and how stable the flow is. The main point is clear separation of responsibilities and deterministic verification.

### E. Deterministic recovery scripts

Use normal Python/shell scripts for tasks that should not depend on model reasoning:

- Health probes.
- Toxiproxy setup/teardown.
- Log filtering and evidence collection.
- Repeatable `git bisect` probes.
- Test result parsing.
- Cloud Run traffic rollback and revision lookup.
- Pass/fail evaluation.
- Evidence receipt generation.

Use AI for diagnosis and code repair where reasoning is valuable, not to replace exact program logic.

---

## 10. Recommended Technology Stack

| Layer | Recommendation | Reason |
|---|---|---|
| Required agent platform | **GitLab Duo Agent Platform** | Core of the project; use a custom flow and focused agent(s). |
| Repository and CI/CD | GitLab Git repository, issues/work items, merge requests, CI/CD | Provides traceability and the automation workflow. |
| Agent context | `AGENTS.md` | Instructs flows about architecture, testing, and safety requirements. |
| Service language/framework | **Python + FastAPI** for the initial service; Express is a valid alternative if the chosen OSS base uses Node.js | Fast to test and straightforward to instrument. Pick one, not both. |
| HTTP client | `httpx` | Provides explicit timeouts and clear request behavior. |
| Resilience utilities | A bounded `tenacity` retry policy or a small explicit implementation; use a circuit-breaker library only if required | Avoid unbounded loops; keep the code easy to reason about. |
| Fault injection | **Toxiproxy** | Repeatable latency/reset conditions in CI. |
| Testing | **pytest** plus the project's existing test framework | Deterministic acceptance checks and regression tests. |
| Test environment | Docker Compose or GitLab CI services | Runs the application, fake dependency, and Toxiproxy in an isolated network. |
| Diagnosis | Git history and GitLab REST APIs; optional GitLab Orbit via MCP | GitLab APIs provide a fallback if Orbit is unavailable. |
| Deployment | **Google Cloud Run** for the Path B live project and optional revision routing | Supports versioned deployments and traffic movement. |
| Container image | GitLab Container Registry or another permitted registry | Repeatable package artifact. |
| Security checks | GitLab SAST and secret detection where available to the provisioned project | Validate the generated change before promotion. |
| Optional metrics | Cloud Monitoring or simple health/latency probes | Measure real outcomes and verify service state. |
| Optional sustainability measurement | GitLab Eco CI | Only if a reliable measured sustainability claim is later added. |

Keep the UI simple. GitLab issues, merge requests, pipeline results, and an evidence report may be sufficient. Build a dashboard only if the core workflow is already complete and the UI materially improves understanding.

---

## 11. GitLab Duo, Triggers, Orbit, and Integration Caveats

### GitLab Duo Agent Platform is mandatory

The core logic must be implemented through real Duo Agent Platform capabilities, not merely mention GitLab in the README. Use a custom flow to orchestrate investigation and remediation, and use GitLab APIs/CI jobs for deterministic operations.

Official documentation:

- [Duo Agent Platform](https://docs.gitlab.com/user/duo_agent_platform/)
- [Flows](https://docs.gitlab.com/user/duo_agent_platform/flows/)
- [Custom flow YAML schema](https://docs.gitlab.com/user/duo_agent_platform/flows/custom_flows_schema/)
- [Flows API](https://docs.gitlab.com/api/duo_agent_platform_flows/)
- [Triggers](https://docs.gitlab.com/user/duo_agent_platform/triggers/)
- [AI Catalog](https://gitlab.com/explore/catalog)

### Do not assume a pipeline event trigger works in the provisioned group

GitLab documentation describes pipeline-event triggers as experimental / feature-flag dependent in the documented trigger history. Check what is enabled for the hackathon project. If a direct pipeline trigger is unavailable, investigate an explicit CI job invoking the supported Flows API or a supported manual/assignment trigger.

Do not build the entire project around an unverified trigger mechanism.

Also, do not assume one bot-created issue, MR, or flow can automatically trigger another flow. Check the actual event rules and permissions. A controlled CI job or a documented Flows API call may be the safer orchestration route.

### GitLab Orbit is an enhancement, not a blocker

Orbit exposes GitLab lifecycle and code relationships as a queryable graph, and can help connect commits, merge requests, source code, pipelines, and dependencies. But Orbit is documented as **beta**, and group enablement/access is a prerequisite. Confirm it is usable in the actual hackathon group before making it a core dependency.

Official documentation:

- [GitLab Orbit](https://docs.gitlab.com/orbit/)
- [Orbit via MCP](https://docs.gitlab.com/orbit/remote/access/mcp/)
- [Orbit query documentation](https://docs.gitlab.com/orbit/remote/queries/)
- [Orbit getting started](https://docs.gitlab.com/orbit/remote/getting-started/)

**Fallback:** use GitLab Commits, Merge Requests, repository files, and Pipeline APIs. The product must still function if Orbit is disabled.

### Credit and time discipline

Project provisioning notes suggest a limited GitLab Credits allocation, reported as 500 credits per month in the research materials. Confirm the actual account balance and limits in the hackathon environment rather than treating that figure as guaranteed.

To conserve resources:

- Filter logs before sending evidence to the model.
- Use deterministic test/probe scripts and `git bisect` instead of asking an LLM to repeatedly inspect the same history.
- Call Duo only for meaningful diagnosis/repair decisions.
- Avoid long autonomous loops.
- Stop after a small, explicit number of repair attempts.
- Store structured evidence between steps instead of resending full logs.

---

## 12. Path B Project Selection

**Recommended path: Path B — Bring Your Own.**

Use a small, existing MIT-licensed FastAPI or Express service that has a genuine downstream HTTP call and can be deployed with Docker. It can be your own existing open-source project or a fork, but the original license and source URL must be verifiable.

Selection checklist:

- [ ] The original repository has a valid MIT license.
- [ ] The app is small enough to understand and test within the remaining time.
- [ ] It has a downstream HTTP dependency that can be routed through a test proxy.
- [ ] It has existing tests or a clear way to add them.
- [ ] Its behavior can be deployed to Cloud Run.
- [ ] It does not require real payment credentials, real customer data, or production access.
- [ ] The project has a clearly documented original source and changes made for this hackathon.
- [ ] All new agentic automation and deployment work is done within the current rules' permitted period (on or after 5 October 2026).
- [ ] The public deployed version can remain available until winners are announced, around 16 November 2026.

Do not claim Path B until a suitable repository is selected and its MIT license is confirmed. If a valid base cannot be established quickly, reassess Path A rather than misrepresenting the provenance of the code.

---

## 13. Risk-Based Autonomy Policy

The project should submit under **Supervised** autonomy.

The agent can perform multi-step investigation, propose and prepare a repair, run checks, and deploy to an isolated staging/candidate environment. A human reviews and approves final promotion or any high-impact action.

The internal risk policy is a key product capability, but it does **not** change the single autonomy level declared for the submission.

| Risk class | Examples | Required behavior |
|---|---|---|
| **Low** | A scoped timeout value, bounded retry policy, or fallback in the affected resilience module | Agent may prepare the change and run it through all tests automatically. The result is still reviewed under the selected Supervised workflow before promotion. |
| **Medium** | Dependency upgrade, wider control-flow change, uncertain ownership, low test coverage | Require extra validation and human outcome/promotion approval. |
| **High** | Authentication, authorization, payment, database schema/migration, secrets, destructive action, wide diff, missing rollback path, unclear diagnosis | Do not auto-merge or promote. Stop and request human review; preserve the stable version. |

### Non-negotiable safety rules

- Run fault injection in a disposable CI/staging environment only.
- Use least-privilege GitLab and Google Cloud identities.
- Never expose production secrets to the model or logs.
- Never permit an unrestricted shell or unrestricted cloud-control tool when a scoped command/API is sufficient.
- Do not let an AI-generated patch approve itself.
- The independent CI pipeline—not the authoring agent—must decide whether objective checks pass.
- Never auto-promote after failing or incomplete tests.
- Never retry non-idempotent operations blindly.
- Never claim recovery while health checks remain unhealthy.
- If cause or repair confidence is insufficient, mark it unknown and stop.
- Limit automated attempts and stop loops after a small, configured number of failures.
- Keep an audit trail of inputs, decisions, action IDs, test results, and promotion/rollback results.
- Allow emergency rollback only through an explicitly permitted, tested recovery action.

---

## 14. Lifecycle Coverage Map

The “Most Stages Covered” prize rewards real post-code lifecycle coverage. The table below shows where FaultForge can touch each stage. Implement the stages in which the project can perform genuine, testable work.

| Stage | FaultForge action | Evidence artifact |
|---|---|---|
| **plan** | Create/update a GitLab incident issue/work item with severity, failure summary, and evidence links | Issue/work item |
| **create** | Prepare a resilience-hardening branch and merge request | Branch, MR, patch |
| **verify** | Run unit tests, regression test, fault replay, and health checks | CI job results and test reports |
| **package** | Build and publish the hardened container image | Image digest/build log |
| **secure** | Run applicable SAST and secret-detection checks | Scan output |
| **release** | Deploy the verified candidate to Cloud Run/staging | Deployment job and revision ID |
| **configure** | Configure Toxiproxy fault profile and, if implemented, candidate/stable traffic routing | Configuration artifact and traffic/deployment result |
| **monitor** | Probe health, error rate, and latency before/after the controlled fault | Structured metrics report |
| **govern** | Enforce risk policy, require the right approval, record result and uncertainty | Risk decision and evidence receipt |

Do not pad stage count with `echo "done"` jobs. If a stage has no real operation or artifact, do not count it. Start with the core stages and extend only after each operation is functional.

---

## 15. Evidence and Measurement Model

FaultForge should use hard measurements, not illustrative values presented as results.

### Required before/after measures

- **Fault reproducibility:** Did the baseline fail under the configured fault?
- **HTTP status/error count:** What proportion of requests failed?
- **Latency:** Record p50/p95/p99 where the number of samples makes the statistic meaningful.
- **Health check:** Did the service meet the declared health criteria?
- **Fix correctness:** Did the same regression test fail before the patch and pass after it?
- **Replay correctness:** Was the exact same fault configuration used after the patch?
- **Stability:** Does the result persist across repeated runs?
- **Recovery time:** How much time elapsed between observed failure and verified recovery?
- **Regression safety:** Did unrelated tests still pass?
- **Security:** Did the relevant scans pass, or did the system accurately report any remaining findings?
- **Policy compliance:** Were high-risk actions stopped for review?
- **Resource use:** Optionally measure runner time or energy, but make no sustainability claim without an appropriate method and measurements.

### Acceptance criteria

Use concrete, configurable thresholds. The numbers below are **proposed test gates**, not performance claims:

1. The unpatched baseline reproduces the defined failure in at least 4 of 5 controlled attempts.
2. The test artifacts identify the exact commit, input, and fault profile used for each run.
3. The incident dossier includes the failing assertion and relevant evidence without exposing secrets.
4. If the workflow claims a confirmed regressing commit, the deterministic probe passes on the earlier known-good revision and fails on the candidate revision.
5. The generated change is presented as a merge request, not pushed directly to protected `main`.
6. Unit tests and the new regression test pass on the candidate branch.
7. The exact fault profile is replayed against the candidate.
8. A proposed gate may require 10 consecutive fault-replay runs to meet the declared expected behavior; record all outcomes, not only the best run.
9. The failure is considered recovered only after an independent health check passes.
10. An unsafe/high-risk change is blocked from automatic promotion.
11. A failed or inconclusive verification does not receive a green/final-success status.
12. The evidence report matches actual pipeline job, commit, deployment, and test outputs.

Choose the thresholds based on the sample application’s real request budget. Do not hard-code a promise such as “0% errors” or “p99 under 145 ms” before measurement. The application may be expected to return a documented fallback during dependency failure; a successful fallback must be distinguished from a healthy upstream dependency.

---

## 16. Incident Dossier Format

Send a small, structured payload to the flow. Keep it concise and link to full artifacts instead of embedding raw output.

Illustrative structure:

```json
{
  "incident_id": "generated-run-id",
  "project_path": "group/project",
  "commit_sha": "candidate-commit",
  "pipeline_url": "https://gitlab.com/...",
  "test_run_id": "chaos-test-run",
  "fault": {
    "type": "latency",
    "target": "shipping-dependency",
    "latency_ms": 3500,
    "jitter_ms": 250,
    "profile_hash": "computed-hash"
  },
  "observations": {
    "health_check": "failed",
    "http_5xx_count": 3,
    "latency_summary": "link-to-measured-artifact"
  },
  "evidence": {
    "failed_test": "tests/chaos/test_resilience.py::test_shipping_timeout",
    "log_excerpt": "sanitized-short-excerpt",
    "relevant_commits": ["commit-sha"],
    "merge_requests": ["merge-request-url"]
  },
  "deployment": {
    "candidate_revision": "if-applicable",
    "known_good_revision": "if-applicable"
  },
  "diagnosis_status": "unknown",
  "notes": "Facts and hypotheses must be separated."
}
```

This is a schema example, not a real incident. The implementation must populate fields from actual pipeline/API output. Do not fabricate identifiers or use unverified data. Store large reports as CI artifacts and include links here.

---

## 17. Repository Structure

A possible layout for the project:

```text
faultforge/
├── AGENTS.md
├── LICENSE
├── README.md
├── .gitlab-ci.yml
├── flows/
│   └── faultforge-flow.yaml
├── app/
│   ├── main.py
│   ├── clients/
│   │   └── shipping_client.py
│   ├── resilience/
│   │   └── policy.py
│   └── health.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── chaos/
│       └── test_resilience.py
├── chaos/
│   ├── docker-compose.chaos.yml
│   └── toxiproxy-config.json
├── scripts/
│   ├── run_fault.py
│   ├── collect_evidence.py
│   ├── diagnose_and_bisect.py
│   ├── evaluate_replay.py
│   ├── generate_receipt.py
│   └── cloudrun_traffic.py
├── infra/
│   └── cloudrun/
├── reports/
│   └── .gitkeep
└── docs/
    ├── architecture.md
    ├── safety-policy.md
    └── measurement-method.md
```

Adapt this structure to the selected MIT-licensed project's conventions. Do not rewrite the original application merely to match this proposed layout.

---

## 18. `AGENTS.md` — Agent Operating Rules

Use repository-specific instructions to keep generated patches consistent and safe. These are policy requirements, not a guarantee that the model will always produce correct code.

Recommended instructions:

1. Reproduce and understand the failure before proposing a fix.
2. Use the supplied incident dossier as evidence; do not invent logs, test results, commit IDs, or deployment state.
3. Separate confirmed facts from hypotheses.
4. Make the smallest change that addresses the demonstrated failure.
5. Prefer bounded network timeouts and explicit error handling.
6. Retry only operations that are safe to retry; use a bounded policy with backoff/jitter.
7. Do not silently swallow exceptions or turn failed dependencies into misleading success responses.
8. Add a regression test reproducing the original fault.
9. Reuse the same Toxiproxy configuration during before/after replay.
10. Do not alter authentication, authorization, payment, schema, migration, secrets, IAM, or destructive-operation code without human approval.
11. Do not commit directly to protected `main`; open a merge request.
12. Do not declare success until the independent CI checks and health checks pass.
13. If evidence is incomplete or the fix cannot be validated, report `UNKNOWN`/`NOT_VERIFIED` and stop.
14. Use only explicitly granted tools and permissions.

---

## 19. Flow Logic and Failure States

Suggested state machine:

```text
READY
  |
  v
BASELINE_VERIFIED
  |
  v
FAULT_INJECTED
  |
  v
FAILURE_CONFIRMED
  |
  v
EVIDENCE_COLLECTED
  |
  v
DIAGNOSIS_COMPLETE_OR_UNKNOWN
  |
  +---- insufficient evidence ----> CONTAINED_NEEDS_REVIEW
  |
  v
REMEDIATION_MR_CREATED
  |
  v
TESTS_AND_FAULT_REPLAY
  |
  +---- any required check fails --> NOT_VERIFIED
  |
  v
CANDIDATE_DEPLOYED_AND_HEALTH_CHECKED
  |
  +---- deployment/health fails ---> RESTORE_OR_KEEP_STABLE
  |
  v
HUMAN_APPROVAL_FOR_PROMOTION
  |
  v
RECOVERED_AND_VERIFIED
  |
  v
EVIDENCE_RECORDED
```

Any timeout, missing permission, invalid evidence, failed security gate, unavailable Orbit service, or exhausted repair attempt must lead to a visible non-success outcome. Never let the flow silently continue to promotion after an error.

---

## 20. MVP Versus Optional Extensions

### MVP — mandatory scope

- [ ] Choose and import one suitable MIT-licensed service for Path B.
- [ ] Run the service and a fake downstream dependency in a repeatable test environment.
- [ ] Configure Toxiproxy to inject the primary latency fault.
- [ ] Demonstrate that the baseline fails predictably.
- [ ] Collect a compact incident dossier from real logs and test outputs.
- [ ] Use a GitLab Duo custom flow for investigation and remediation planning.
- [ ] Use GitLab APIs to inspect relevant repository history and create a merge request.
- [ ] Add a resilience fix and a regression test.
- [ ] Replay the same fault after the patch and evaluate the outcome deterministically.
- [ ] Keep failed/uncertain candidates from being promoted.
- [ ] Build and deploy the application to a public staging/Cloud Run environment for Path B.
- [ ] Provide a report containing actual test outcomes and risk decisions.
- [ ] Keep the project within the selected Supervised autonomy model.

### Stretch — only after the MVP works

1. **Cloud Run canary and rollback:** Deploy a candidate revision, observe independent health checks, and route traffic back to the last known-good revision if the gate fails.
2. **Orbit context:** Use the graph to connect the incident to relevant code, merge requests, pipeline history, and dependencies.
3. **Second fault:** Add connection reset/503 only after primary latency testing is stable.
4. **Autonomy policy refinement:** Add explicit path-based risk classification and richer approval rules.
5. **More lifecycle coverage:** Add only stages where real operations and useful artifacts can be shown.
6. **Resource/energy measurement:** Consider Eco CI only if resource savings are measurable and this does not weaken the core reliability workflow.
7. **Small status interface:** Add a UI only if GitLab-native issues/MRs/pipeline pages cannot make the workflow understandable.

### Out of scope for the first version

- Arbitrary fault diagnosis across all languages/frameworks.
- Multiple repositories or coordinated cross-repo migrations.
- Automatic database-schema or payment/authentication changes.
- Many independent agent services.
- Continuous unrestricted production remediation.
- A separate FinOps, sustainability, test-optimizer, or compliance product.
- A large dashboard before the workflow works.
- Pretending all nine stages are implemented when some are empty placeholders.

---

## 21. Known Risks and Mitigations

| Risk | Why it matters | Mitigation |
|---|---|---|
| Orbit unavailable in the hackathon group | Diagnosis could stall if the project depends on graph access | Verify early; provide a GitLab Commits/MR API fallback. |
| Flow trigger or API permission unavailable | The core agent may not start automatically | Test the actual supported trigger and authentication immediately; have a supported CI/API or manual fallback. |
| Toxiproxy setup becomes unstable | The core evidence depends on reproducible failure injection | Start with Docker Compose/GitLab CI services and one network fault. |
| `git bisect` finds no meaningful culprit | The injected fault may affect every revision equally | Only use bisect when the same probe distinguishes good and bad commits; otherwise report a suspected weakness. |
| AI generates a patch that hides symptoms | A green result may not mean the service is resilient | Require a regression test, same-fault replay, health checks, and normal tests. |
| Retries worsen an outage | Retry storms can amplify dependency failures | Use bounded retries, backoff/jitter, timeouts, and idempotency-aware policies. |
| Cloud Run permissions or traffic management are delayed | Deployment and rollback can consume the build window | Verify GCP access early; keep CI fault/replay independent from cloud-specific steps. |
| Too many features | The complete workflow may not be finished in time | One service, one primary fault, one flow, one resilience fix. |
| Too many agent calls or oversized evidence | Credits and runtime may be consumed | Filter logs deterministically; invoke Duo once with a concise dossier; cap retries. |
| False success or fabricated metrics | Damages trust and weakens the technical argument | Generate claims only from CI/API artifacts; preserve `UNKNOWN` and failed states. |
| Safety policy conflicts with the declared autonomy level | It may be misclassified as Hands-off when humans approve promotion | Declare **Supervised** and keep the product behavior consistent with it. |
| Path B source/licensing is unclear | Eligibility may be jeopardized | Verify the original MIT license and record the upstream repository before starting. |

---

## 22. Focused Prize Strategy

### Primary: Path B — Best Supervised Agent ($4,000)

Why this is the best fit for the chosen product:

- The automation executes meaningful multi-step work.
- Diagnosis and repair happen through GitLab Duo.
- CI validates the patch independently.
- Cloud/staging operations are constrained by explicit rules.
- A human approves the final promotion or high-risk actions.
- The workflow can stop and report uncertainty rather than claim success.

**Do not switch to Hands-off only because the prize is $1,000 higher.** A Hands-off submission must behave as a no-intermediate-human workflow. FaultForge's safety model is more credible as Supervised in the time available.

### Secondary: Path B — Most Stages Covered ($5,000)

Build genuine operations across as much of the nine-stage lifecycle as feasible, while maintaining a coherent use case. Coverage is a consequence of the workflow, not a list of empty CI labels.

### Additional: Most Creative ($4,000)

The strongest idea-level differentiator is the loop:

**Controlled failure → evidence-backed diagnosis → safe containment → AI-assisted hardening → identical-fault replay → independent proof.**

The claim should be narrower than “the first self-healing agent.” Competing projects exist. The evidence-backed same-fault replay is the specific capability FaultForge must implement exceptionally well.

### Google Cloud bonus (up to +0.2)

Use Cloud Run if the deployment can be made reliable and accessible. Commit the deployment/IaC code to the public GitLab repository and provide the required live URL. Validate the requirements on the current official page.

### Sustainability award — not a launch priority

The environmental prize requires the submission to quantify actual sustainability gains using recognized public methodologies and SCI. Do not add carbon claims based on rough estimates or merely count fewer retries. If time permits, use Eco CI measurements over repeated comparable runs and distinguish measurement from estimation. Otherwise leave this prize out of the core plan.

---

## 23. Success Definition

FaultForge is considered a credible MVP when it can repeatedly perform all of the following:

1. Run an identifiable service and dependency in a controlled environment.
2. Inject a fixed, documented fault.
3. Prove that the original version fails under that condition.
4. Collect valid evidence and identify the relevant weakness without inventing certainty.
5. Use GitLab Duo Agent Platform in a meaningful investigation/remediation flow.
6. Prepare a scoped resilience-hardening merge request.
7. Add a test that reproduces the original failure.
8. Run ordinary tests and replay the same fault profile.
9. Determine success/failure from machine-readable results rather than model opinion.
10. Keep a failed or unsafe candidate from promotion.
11. Deploy the verified project as required for Path B.
12. Leave a traceable incident/MR/pipeline record of what actually happened.

The product is **not finished** if the agent merely writes a plausible patch, if the same fault was not replayed, if a failure is silently ignored, or if the app is declared healthy without an independent check.

---

## 24. Decision Log — Keep These Decisions Stable

Unless feasibility tests prove otherwise, treat the following as the project's current decisions:

- **Product:** FaultForge — “Break It, Heal It”.
- **Problem:** An app breaks under a controlled downstream dependency failure because resilience behavior is missing or insufficient.
- **Unique proof:** The same fault breaks the baseline and is replayed against the hardened candidate.
- **Path:** Path B, contingent on verifying an existing MIT-licensed upstream project.
- **Declared autonomy:** Supervised.
- **Primary prize:** Path B Best Supervised Agent.
- **Secondary prize:** Path B Most Stages Covered.
- **Additional prize opportunity:** Most Creative.
- **Deployment bonus:** Google Cloud, if the deployment is stable, public, and documented.
- **Framework:** Python + FastAPI unless the selected MIT base strongly favors Node.js/Express.
- **Fault tool:** Toxiproxy in CI/integration testing.
- **Agent platform:** GitLab Duo Agent Platform custom flow.
- **Diagnosis fallback:** GitLab Commits/MR APIs if Orbit is unavailable.
- **First fault:** Slow downstream HTTP dependency.
- **Second fault:** Optional transient connection reset/503, only after MVP completion.
- **Primary safety rule:** No production or high-impact promotion without the required approval and independent verification.
- **Scope rule:** One service, one primary fault, one custom flow, one verified fix before adding more.

Any change to these decisions should be justified by a concrete access/feasibility test, not by adding features because they sound impressive.

---

## 25. Essential Official References

### Hackathon

- [Life After Code — official event page](https://gitlab-transcend.devpost.com/?ref_medium=discover)
- [Hackathon resources](https://gitlab-transcend.devpost.com/resources)
- [Official rules](https://gitlab-transcend.devpost.com/rules)

### GitLab agent platform

- [GitLab Duo Agent Platform](https://docs.gitlab.com/user/duo_agent_platform/)
- [Flows](https://docs.gitlab.com/user/duo_agent_platform/flows/)
- [Custom flow YAML schema](https://docs.gitlab.com/user/duo_agent_platform/flows/custom_flows_schema/)
- [Flow API](https://docs.gitlab.com/api/duo_agent_platform_flows/)
- [Triggers](https://docs.gitlab.com/user/duo_agent_platform/triggers/)
- [GitLab AI Catalog](https://gitlab.com/explore/catalog)

### Context and fault testing

- [GitLab Orbit](https://docs.gitlab.com/orbit/)
- [Orbit MCP access](https://docs.gitlab.com/orbit/remote/access/mcp/)
- [Shopify Toxiproxy](https://github.com/Shopify/toxiproxy)

### Deployment and optional sustainability

- [Google Cloud Run rollback and traffic migration](https://docs.cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration)
- [GitLab Eco CI](https://docs.gitlab.com/ci/sustainability/eco_ci/)

---

## Final Principle

**FaultForge must prove resilience, not merely generate a fix.**

The project should be judged by whether it can reproduce a meaningful failure, gather credible evidence, take a safe and traceable action, improve the code, and independently demonstrate that the same failure no longer causes the original problem.

Everything else—more agents, more faults, a wider dashboard, more stages, or sustainability extras—is secondary until that complete loop works.
