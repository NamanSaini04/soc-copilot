import json
from pathlib import Path

from app.service import IncidentService

ROOT = Path(__file__).resolve().parents[1]


def evaluate() -> dict:
    service = IncidentService()
    labels = json.loads((ROOT / "evaluation" / "labelled_cases.json").read_text())
    rows = []
    for case in labels:
        result = service.investigate(case["alert_id"])
        rows.append({
            "alert_id": case["alert_id"],
            "type_correct": result.alert_type == case["expected_type"],
            "severity_correct": result.severity.value == case["expected_severity"],
            "mitre_correct": case["expected_mitre"] in {m["technique_id"] for m in result.mitre_attack},
            "has_citations": bool(result.citations),
            "all_actions_gated": all(r.requires_approval for r in result.recommendations),
        })
    n = len(rows)
    metrics = {key: sum(r[key] for r in rows)/n for key in rows[0] if key != "alert_id"}
    output = {"sample_size": n, "metrics": metrics, "cases": rows,
              "warning": "Small synthetic test set; results demonstrate instrumentation, not production efficacy."}
    (ROOT / "evaluation" / "results.json").write_text(json.dumps(output, indent=2))
    return output


if __name__ == "__main__": print(json.dumps(evaluate(), indent=2))

