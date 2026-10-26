# Security policy

This repository is a **defensive synthetic-data demonstration**. Do not add
real production telemetry, credentials, real employee identities, or operational
security-system connectivity to the public repository.

## Public Streamlit-only demo

A public Streamlit demo may be hosted **only** with the bundled synthetic
fixtures and in-memory per-browser `IncidentService(persist=False)`.
An approval is a review-record update; no operational account changes, network
blocking, device isolation, live ticket creation, or external action occurs.
Public demo records are intentionally session-scoped and ephemeral.

This is not a proof of secure multi-user isolation or resilience against a
hostile workload. Hosting should be tested with separate browser sessions and
the approved deployment flow in `docs/demo_deployment.md`.

## Local FastAPI and MCP helpers

The local FastAPI requires `SOC_API_TOKEN` for its protected endpoints
and binds to `127.0.0.1` using `python main.py`. This single static token is
**not** production identity or access management.

Never expose the local FastAPI, MCP helper servers, JSON incident store,
or their ports to the public internet. Those helpers are not designed for a
multi-tenant production deployment.

## Reporting a vulnerability

Use GitHub private vulnerability reporting/security advisories. Never post
tokens, real alerts, personal information, or logs containing secrets publicly.

## Production prerequisites (not claimed or implemented)

Independent labelled incident evaluation including benign/missing-data cases,
identity/OIDC and role/tenant authorization, secure durable database,
immutable audit history, encrypted secrets and transit, rate limiting,
security testing, retention/deletion controls, monitoring, incident recovery,
and independent safeguards at **any** operational response-execution layer.
Real SIEM integration must be expressly authorized and initially read-only.
