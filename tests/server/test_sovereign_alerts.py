"""Test Suite for Sovereign Indian Agency Integration Webhooks (ISRO/IMD/INCOIS/NCPOR).

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Verifies:
1. Sovereign gateway status and supported agency registry.
2. OASIS CAP v1.2 alert formatting and HMAC-SHA256 cryptographic signing.
3. Ingress of signed alerts from mainland command (NCPOR/ISRO/IMD/INCOIS).
4. Rejection of tampered / invalid signatures with 401 Unauthorized.
5. Dynamic agency webhook registration and configuration updates.
"""

from __future__ import annotations

import json
import pytest
from fastapi.testclient import TestClient

from backend.server.app import create_app
from backend.server.routes.alerts_sovereign import (
    SovereignAgency,
    _AGENCY_WEBHOOKS,
    compute_sovereign_hmac,
)
from backend.server.state import reset_server_state


@pytest.fixture
def test_client() -> TestClient:
    """Fixture providing initialized FastAPI test client."""
    reset_server_state()
    app = create_app()
    return TestClient(app)


def test_sovereign_gateway_status_and_agencies(test_client: TestClient) -> None:
    """Verify status and agency listings for NCPOR, ISRO, IMD, and INCOIS."""
    # 1. Status
    resp_stat = test_client.get("/api/alerts/sovereign/status")
    assert resp_stat.status_code == 200
    stat_data = resp_stat.json()
    assert stat_data["status"] == "OPERATIONAL"
    assert stat_data["registered_agencies_count"] >= 4

    # 2. Agencies
    resp_agencies = test_client.get("/api/alerts/sovereign/agencies")
    assert resp_agencies.status_code == 200
    agencies_data = resp_agencies.json()
    agency_names = [a["agency"] for a in agencies_data["agencies"]]
    assert "NCPOR" in agency_names
    assert "ISRO_ISTRAC" in agency_names
    assert "IMD" in agency_names
    assert "INCOIS" in agency_names


def test_sovereign_cap_alert_dispatch(test_client: TestClient) -> None:
    """Verify formatting and cryptographic HMAC signing of outbound CAP alerts."""
    resp = test_client.post(
        "/api/alerts/sovereign/dispatch",
        json={
            "agency": "ISRO_ISTRAC",
            "category": "Infra",
            "event": "LEO Ground Station Antenna Pre-Pass Alignment",
            "severity": "Moderate",
            "headline": "Cartosat-2F Pass Preparation Ready at Larsemann Hills",
            "description": "Antenna radome de-iced; dual-axis tracking locked on az 142.5 deg.",
            "station_id": "bharati",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ALERT_DISPATCHED"
    assert data["agency"] == "ISRO_ISTRAC"
    assert "signature_header" in data
    assert data["signature_header"].startswith("sha256=")

    # Verify CAP v1.2 payload integrity
    cap = data["cap_payload"]
    assert cap["sender"] == "friday.bharati.antarctica@ncpor.res.in"
    assert cap["event"] == "LEO Ground Station Antenna Pre-Pass Alignment"
    assert len(cap["hmac_sha256"]) == 64


def test_sovereign_alert_ingress_authenticated(test_client: TestClient) -> None:
    """Verify ingestion of authentic, HMAC-signed alert from mainland HQ."""
    secret = _AGENCY_WEBHOOKS[SovereignAgency.NCPOR]["secret_key"]
    payload = {
        "agency": "NCPOR",
        "identifier": "NCPOR-CMD-2026-089",
        "headline": "Urgent Pre-Winter Fuel Conservation Directive",
        "severity": "Severe",
        "instruction": "Reduce non-essential research laboratory heating setpoints by 2.0°C.",
    }

    # Compute valid signature
    sig = compute_sovereign_hmac(payload, secret)

    resp = test_client.post(
        "/api/alerts/sovereign/ingress",
        json=payload,
        headers={"X-FRIDAY-Signature": f"sha256={sig}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ALERT_INGESTED"
    assert data["agency"] == "NCPOR"
    assert data["identifier"] == "NCPOR-CMD-2026-089"


def test_sovereign_alert_ingress_tampered_rejected(test_client: TestClient) -> None:
    """Verify spoofed or tampered alerts are rejected with 401 Unauthorized."""
    payload = {
        "agency": "IMD",
        "headline": "Spoofed False Blizzard Warning",
        "severity": "Extreme",
    }
    # Send forged signature
    resp = test_client.post(
        "/api/alerts/sovereign/ingress",
        json=payload,
        headers={"X-FRIDAY-Signature": "sha256=0000000000000000000000000000000000000000000000000000000000000000"},
    )
    assert resp.status_code == 401
    assert "mismatch" in resp.json()["detail"].lower()


def test_sovereign_webhook_registration(test_client: TestClient) -> None:
    """Verify dynamic update of agency target webhook URL and cryptographic key."""
    resp = test_client.post(
        "/api/alerts/sovereign/register-webhook",
        json={
            "agency": "INCOIS",
            "target_url": "https://new-endpoint.incois.gov.in/api/v2/seaice",
            "secret_key": "incois_updated_2026_super_secret_key",
            "active": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "CONFIG_UPDATED"
    assert data["agency"] == "INCOIS"
    assert data["target_url"] == "https://new-endpoint.incois.gov.in/api/v2/seaice"
