# Running and publishing the SOC Copilot safely

## Status and boundaries

This branch is a **complete demo workflow** on three labelled synthetic alerts,
not a fully validated production SOC. It never contacts real SIEM systems, changes
security controls, opens real tickets, or invokes account resets/host isolation.
The Streamlit dashboard uses an `IncidentService(persist=False)` per browser
session. The local FastAPI has a separate token-gated, file-backed store.

## Local quickstart (Python 3.12)

```bash
git clone https://github.com/NamanSaini04/soc-copilot.git
cd soc-copilot
# If testing the unpublished branch:
git switch soc-demo-hardening-v2
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"
pytest -q
python evaluation/evaluate.py
streamlit run dashboard/streamlit_app.py
```

In your browser: select ALT-001, click **Run investigation**, inspect the
evidence and citations, enter an analyst name, record a review decision,
and download both JSON and PDF. Repeat ALT-002 and ALT-003.

## Deploy a **public synthetic demo** to Streamlit Community Cloud

This step requires the repo owner's GitHub and Streamlit account.

1. Visit https://share.streamlit.io/ and sign in using GitHub.
2. Select **Create app** → deploy from GitHub.
3. Set repository to `NamanSaini04/soc-copilot`, branch
   `soc-demo-hardening-v2` (until merged), and main file
   `dashboard/streamlit_app.py`.
4. Choose Python 3.12 if asked. The file `dashboard/requirements.txt`
   installs just the dashboard's dependencies.
5. Choose a shareable subdomain and deploy.
6. Open the hosted app in an incognito browser; test all three fixture alerts,
   approve and reject a recommendation, and download a report.
7. Confirm an unrelated incognito browser session cannot read the first
   browser's incident or approval state.
8. Put the **actual verified URL**, not a guessed link, on your portfolio.

This is a deliberately harmless demo using generated alert fixtures and local
playbooks only. Do not add company telemetry, real client data, passwords or API
keys to the repo or enter them in the hosted UI. Hosted apps may reboot; review
decisions are temporary and are not stored across browser sessions.

## Optional local FastAPI (do not expose to public internet)

```bash
export SOC_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
python main.py
curl http://127.0.0.1:8000/health
curl -H "X-SOC-Demo-Token: $SOC_API_TOKEN" http://127.0.0.1:8000/alerts
curl -X POST -H "X-SOC-Demo-Token: $SOC_API_TOKEN" http://127.0.0.1:8000/investigations/ALT-001
```

Set the environment variable in your shell. Do not commit or paste it into
public issues, documentation or screenshots. The demo API binds to 127.0.0.1.
Without a configured token, its protected routes return HTTP 503. Requests
with an invalid token return 401. Production authentication requires OIDC,
role-based scopes, robust authorization, rate limits and audited persistence.

## Acceptance checklist

- [ ] GitHub CI passes both `ruff check .` and `pytest -q`.
- [ ] Existing three labelled cases pass with explicit sample-size caveat.
- [ ] All fixture alerts run from the dashboard.
- [ ] Evidence, hypotheses, provisional mapping, citations and risk appear.
- [ ] Reviewing recommendations creates a dated audit event but **does not**
      execute any action.
- [ ] Review decisions survive local API restart; public dashboard sessions
      remain isolated and ephemeral.
- [ ] JSON and PDF exports download and render correctly.
- [ ] Published Streamlit link verified by a browser.
- [ ] Portfolio status stays **Functional synthetic-data demo**, not
      'production SOC' or validated threat-detection efficacy.

## What is still required for a production product

A real operational service would additionally need independently labelled
evaluation datasets, test coverage of benign/ambiguous cases, tenant-specific
identity/RBAC, secure persistent database and immutable audit events, secrets
management, rate limits, reliable queues and retries, monitoring/backups, and
authorized **read-only** lab integration before even considering response
connectors. Any live response commands require a separate, independently
tested approval and execution boundary.
