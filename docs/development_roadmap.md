# Development roadmap and completion criteria

| Phase | Objective and decision | Tests | Completion criteria | Status |
|---|---|---|---|---|
| 1. Architecture/data | Define trust boundaries; use small synthetic fixtures | Schema validation | Data provenance and scope documented | Complete |
| 2. Ingestion/dashboard | Normalize alerts and provide analyst selection | Load all fixtures | Alerts and summary charts render | Complete |
| 3. Triage | Reproducible category and severity baseline | Determinism, labelled cases | Structured triage result with rationale | Complete |
| 4. RAG | Retrieve controlled playbooks with source IDs | Known-query retrieval | Ranked chunks, score threshold, citations | Complete baseline |
| 5. Investigation/risk | Correlate evidence and calculate explicit risk | Evidence provenance, score bounds | Evidence/hypothesis separation | Complete |
| 6. MCP | Expose narrow read and draft tools | Schema and bound checks | No unapproved operational tool | Complete baseline |
| 7. Orchestration | Audited hand-offs and shared state | End-to-end case | Agent trace persisted | Complete |
| 8. Incident reporting | Structured investigation record | Required fields | JSON report generated | Complete |
| 9. Incident PDF | Recruiter-readable case output | Render and visual inspection | Readable multi-page PDF | Complete |
| 10. Evaluation | Instrument classification, mapping, citations, gating | Labelled cases | Machine-readable results with caveat | Complete baseline |
| 11-12. Technical report | Explain design, results, risk, limitations | Text and PDF checks | Professional portfolio PDF | Complete |
| 13. Hardening/deploy | CI, auth, secrets, rate limits, persistent DB | Integration/security tests | Required before public deployment | Planned |

## Recommended next iteration

1. Expand to at least 100 independently labelled incidents with ambiguous and benign cases.
2. Add sentence-transformer embeddings and compare against the TF-IDF baseline using Recall@k, MRR, citation precision, and latency.
3. Add a real LangGraph checkpointer when persistent, interruptible sessions are required.
4. Connect an approved read-only SIEM lab and a licensed threat-intelligence source.
5. Add OIDC, role-based scopes, secrets management, structured audit logging, rate limits, and retention controls before deployment.

