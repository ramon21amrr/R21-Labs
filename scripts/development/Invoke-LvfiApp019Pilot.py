"""Run the non-financial APP-019 technical-pilot journey against a disposable DB.

The runner never opens or writes the Oracle workbook.  It checks its SHA-256
before and after the journey, uses only HTTP contracts, and stores private,
sanitized evidence outside version control.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from lvfi_api.application.local_admin_authentication import (
    LocalAdminAuthenticationService,
)
from lvfi_api.config import Settings
from lvfi_api.infrastructure.database import Database
from lvfi_api.main import create_app

ORACLE_SHA256 = "FDCA46B855CC3FA28A34F622D282221F9B8E3EA41B0B6664432D9614D45D3924"
M2_QUERY = {
    "sample_size": 5,
    "context": "venue",
    "season_scope": "current",
    "metric": "goals_scored",
}
M3_QUERY = {
    "sample_size": 5,
    "competition_scope": "target_competition",
    "season_scope": "current",
    "metric": "goals_scored",
    "comparator": "at_least",
    "achievement_target": 1,
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _require(response: Any, status: int, operation: str) -> dict[str, Any]:
    if response.status_code != status:
        raise RuntimeError(f"{operation} returned HTTP {response.status_code}")
    return response.json()


def _complete(sample: dict[str, Any]) -> bool:
    return bool(sample["home_sample"]["complete"] and sample["away_sample"]["complete"])


def _json_sha256(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def _used_match_ids(sample: dict[str, Any]) -> list[int]:
    """Preserve only the selected IDs from an already-returned public sample."""
    return list(sample["used_match_ids"])


def _method_two_samples(result: dict[str, Any]) -> dict[str, list[int]]:
    evidence = result["payload"]["evidence"]
    return {
        name: _used_match_ids(evidence[name]["sample"])
        for name in (
            "home_production",
            "away_complement",
            "away_production",
            "home_complement",
            "home_production_reference",
            "away_complement_reference",
            "away_production_reference",
            "home_complement_reference",
        )
    }


def _method_three_samples(result: dict[str, Any]) -> dict[str, list[int]]:
    payload = result["payload"]
    return {
        "home": _used_match_ids(payload["home"]["sample"]),
        "away": _used_match_ids(payload["away"]["sample"]),
    }


def _all_matches(client: TestClient, competition_id: int) -> list[dict[str, Any]]:
    first = _require(
        client.get(
            "/matches",
            params={"competition_id": competition_id, "page": 1, "page_size": 100},
        ),
        200,
        "matches",
    )
    matches = list(first["items"])
    total = first["total"]
    for page in range(2, (total + 99) // 100 + 1):
        result = _require(
            client.get(
                "/matches",
                params={"competition_id": competition_id, "page": page, "page_size": 100},
            ),
            200,
            "matches",
        )
        matches.extend(result["items"])
    return matches


async def _bootstrap(settings: Settings, password: str) -> None:
    database = Database(settings)
    await database.start()
    try:
        await LocalAdminAuthenticationService(database).bootstrap(password)
    finally:
        await database.stop()


def _analysis_evidence(
    client: TestClient, match: dict[str, Any], oracle: Path, sequence: int
) -> dict[str, Any] | None:
    started = time.monotonic()
    match_id = match["id"]
    sample = _require(
        client.get(f"/matches/{match_id}/method-one/sample"), 200, "method-one sample"
    )
    if not _complete(sample):
        return None
    statistics = _require(client.get(f"/matches/{match_id}/statistics"), 200, "statistics")
    configuration = _require(
        client.get(f"/matches/{match_id}/configuration/effective"),
        200,
        "effective configuration",
    )
    method_two = _require(
        client.get(f"/matches/{match_id}/method-two/result", params=M2_QUERY),
        200,
        "method two",
    )
    method_three = _require(
        client.get(f"/matches/{match_id}/method-three/result", params=M3_QUERY),
        200,
        "method three",
    )
    if _sha256(oracle) != ORACLE_SHA256:
        raise RuntimeError("oracle SHA-256 changed during pilot")

    key = f"app019-{match['competition']['id']}-{match['season']['id']}-{match_id}"
    execution = _require(
        client.post(
            f"/matches/{match_id}/method-one/pricing-executions",
            headers={"Idempotency-Key": key},
        ),
        201,
        "method-one execution",
    )
    if execution["status"] != "completed":
        raise RuntimeError("method-one execution is not completed")
    analysis = _require(
        client.post(f"/matches/{match_id}/analyses"), 201, "analysis draft"
    )
    calculated = _require(
        client.post(
            f"/analyses/{analysis['analysis_id']}/calculate",
            json={"execution_id": execution["execution_id"]},
        ),
        200,
        "analysis calculation",
    )
    reviewed = _require(
        client.post(
            f"/analyses/{analysis['analysis_id']}/reviews",
            json={"reason": "APP-019 technical pilot review"},
        ),
        200,
        "analysis review",
    )
    approval = _require(
        client.post(
            f"/analyses/{analysis['analysis_id']}/approve",
            json={"reason": "APP-019 technical pilot approval"},
        ),
        200,
        "analysis approval",
    )
    snapshot = approval["snapshot"]
    loaded_snapshot = _require(
        client.get(f"/analyses/{analysis['analysis_id']}/snapshot"),
        200,
        "analysis snapshot",
    )
    if loaded_snapshot["snapshot_hash"] != snapshot["snapshot_hash"]:
        raise RuntimeError("snapshot hash changed after approval")
    pdf = _require(
        client.post(f"/analysis-snapshots/{snapshot['snapshot_id']}/pdfs"),
        201,
        "PDF generation",
    )
    downloaded = client.get(f"/analysis-pdfs/{pdf['artifact_id']}/download")
    if downloaded.status_code != 200:
        raise RuntimeError("PDF download failed")
    downloaded_sha256 = hashlib.sha256(downloaded.content).hexdigest()
    if downloaded_sha256 != pdf["sha256"]:
        raise RuntimeError("downloaded PDF checksum mismatch")
    reproduction = _require(
        client.post(
            f"/pricing-executions/{execution['execution_id']}/reproductions"
        ),
        201,
        "execution reproduction",
    )
    if reproduction["outcome"] != "exact_match":
        raise RuntimeError("pricing execution reproduction is not exact")
    history = _require(
        client.get(f"/matches/{match_id}/analyses"), 200, "analysis audit history"
    )
    if not any(item["analysis_id"] == analysis["analysis_id"] for item in history["analyses"]):
        raise RuntimeError("analysis is absent from audit history")
    return {
        "analysis_key": key,
        "sequence": sequence,
        "match_id": match_id,
        "competition_id": match["competition"]["id"],
        "season_id": match["season"]["id"],
        "oracle_comparison": {
            "status": "unavailable",
            "reason": "approved workbook has no reproducible target/cutoff/output mapping",
            "oracle_sha256": ORACLE_SHA256,
        },
        "import_data": {
            "source_sha256": ORACLE_SHA256,
            "statistics_response_sha256": _json_sha256(statistics),
        },
        "samples": {
            "method_one_complete": True,
            "method_one_fingerprint": execution["sample_fingerprint"],
            "method_one_response_sha256": _json_sha256(sample),
            "method_one_home_match_ids": [
                item["match"]["id"] for item in sample["home_sample"]["matches"]
            ],
            "method_one_away_match_ids": [
                item["match"]["id"] for item in sample["away_sample"]["matches"]
            ],
        },
        "methods": {
            "method_one_version": execution["method_one_version"],
            "method_two_version": method_two["method_version"],
            "method_three_version": method_three["method_version"],
            "method_two_query": M2_QUERY,
            "method_three_query": M3_QUERY,
            "method_two_sample_match_ids": _method_two_samples(method_two),
            "method_three_sample_match_ids": _method_three_samples(method_three),
            "method_two_response_sha256": _json_sha256(method_two),
            "method_three_response_sha256": _json_sha256(method_three),
            "method_two_result_fingerprint": method_two["payload"]["result_fingerprint"],
        },
        "configuration": {
            "effective_hash": configuration["effective_hash"],
            "response_sha256": _json_sha256(configuration),
        },
        "workflow": {
            "calculated_status": calculated["status"],
            "reviewed_status": reviewed["status"],
            "approved_status": approval["analysis"]["status"],
            "analysis_id": analysis["analysis_id"],
            "snapshot_id": snapshot["snapshot_id"],
            "snapshot_hash": snapshot["snapshot_hash"],
        },
        "pdf": {
            "artifact_id": pdf["artifact_id"],
            "sha256": pdf["sha256"],
            "download_sha256": downloaded_sha256,
        },
        "audit": {
            "reproduction": reproduction["outcome"],
            "execution_id": execution["execution_id"],
            "workflow_events": approval["analysis"]["events"],
        },
        "operational_observations": {
            "duration_ms": round((time.monotonic() - started) * 1000),
            "usability": "not_assessed_no_human_session",
            "rework_count": 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--pdf-storage", type=Path, required=True)
    parser.add_argument("--import-accepted", type=int, required=True)
    parser.add_argument("--import-rejected", type=int, required=True)
    parser.add_argument("--environment-reprovisions", type=int, default=0)
    arguments = parser.parse_args()
    if _sha256(arguments.oracle) != ORACLE_SHA256:
        raise RuntimeError("oracle SHA-256 mismatch before pilot")
    database_url = os.environ.get("LVFI_DATABASE_URL")
    if not database_url:
        raise RuntimeError("LVFI_DATABASE_URL is required")
    arguments.pdf_storage.mkdir(parents=True, exist_ok=True)
    settings = Settings(
        environment="pilot",
        app_name="lvfi-app-019-pilot",
        database_url=database_url,
        log_level="ERROR",
        pdf_storage_dir=arguments.pdf_storage,
        pdf_renderer_script=Path(__file__).resolve().parents[1]
        / "local"
        / "render-lvfi-pdf.mjs",
    )
    password = secrets.token_urlsafe(24)
    asyncio.run(_bootstrap(settings, password))
    evidence: list[dict[str, Any]] = []
    failures: list[str] = []
    with TestClient(create_app(settings)) as client:
        _require(client.get("/health"), 200, "health")
        _require(client.get("/ready"), 200, "readiness")
        _require(client.post("/auth/login", json={"password": password}), 200, "login")
        competitions = _require(
            client.get("/competitions", params={"page": 1, "page_size": 100}),
            200,
            "competitions",
        )["items"]
        for competition in competitions:
            if len({item["competition_id"] for item in evidence}) >= 5:
                break
            accepted_here = 0
            matches = _all_matches(client, competition["id"])
            for match in matches:
                if accepted_here >= 4 or len(evidence) >= 20:
                    break
                if not match["has_statistics"]:
                    continue
                try:
                    item = _analysis_evidence(client, match, arguments.oracle, len(evidence) + 1)
                except RuntimeError as error:
                    failures.append(f"match_id={match['id']}: {error}")
                    continue
                if item is not None:
                    evidence.append(item)
                    accepted_here += 1
    if len(evidence) < 20:
        detail = "; ".join(failures[:10]) or "no eligible complete samples"
        raise RuntimeError(
            f"pilot yielded {len(evidence)}/20 technical analyses; {detail}"
        )
    if _sha256(arguments.oracle) != ORACLE_SHA256:
        raise RuntimeError("oracle SHA-256 changed after pilot")
    arguments.evidence.parent.mkdir(parents=True, exist_ok=True)
    arguments.evidence.write_text(
        json.dumps(
            {
                "oracle_path": str(arguments.oracle),
                "oracle_sha256": ORACLE_SHA256,
                "source_import": {
                    "accepted_records": arguments.import_accepted,
                    "rejected_records": arguments.import_rejected,
                    "source_sha256": ORACLE_SHA256,
                },
                "pilot_run_observations": {
                    "environment_reprovisions": arguments.environment_reprovisions,
                    "usability": "not_assessed_no_human_session",
                },
                "technical_analyses": evidence,
                "technical_analysis_count": len(evidence),
                "competition_count": len({item["competition_id"] for item in evidence}),
                "valid_oracle_comparison_count": 0,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
