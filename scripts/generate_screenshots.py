"""Script to run a lightweight local mock server and capture frontend screenshots using Chrome headless."""

import http.server
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "frontend" / "dist"
SCREENSHOTS_DIR = BASE_DIR / "docs" / "screenshots"

MOCK_OVERVIEW = {
    "total_contracts": 14,
    "active_contracts": 12,
    "total_runs": 1420,
    "passed_runs": 1338,
    "failed_runs": 82,
    "pass_rate": 94.2,
    "unreviewed_failures": 3,
    "recent_runs": [
        {
            "id": "run-019a8b2c-3d4e-7001",
            "contract_id": "c-001",
            "contract_name": "Customer Support Ticket Schema",
            "contract_version_id": "cv-001-v2",
            "contract_version_number": 2,
            "status": "passed",
            "failed_checks": 0,
            "total_checks": 6,
            "duration_ms": 14.2,
            "review_status": "reviewed",
            "created_at": "2026-10-19T23:15:00Z"
        },
        {
            "id": "run-019a8b2c-3d4e-7002",
            "contract_id": "c-002",
            "contract_name": "Financial Transaction Policy",
            "contract_version_id": "cv-002-v1",
            "contract_version_number": 1,
            "status": "failed",
            "failed_checks": 2,
            "total_checks": 8,
            "duration_ms": 22.8,
            "review_status": "unreviewed",
            "created_at": "2026-10-19T23:10:00Z"
        },
        {
            "id": "run-019a8b2c-3d4e-7003",
            "contract_id": "c-003",
            "contract_name": "Tool Call Policy & Param Allowlist",
            "contract_version_id": "cv-003-v3",
            "contract_version_number": 3,
            "status": "passed",
            "failed_checks": 0,
            "total_checks": 5,
            "duration_ms": 9.5,
            "review_status": "reviewed",
            "created_at": "2026-10-19T22:58:00Z"
        },
        {
            "id": "run-019a8b2c-3d4e-7004",
            "contract_id": "c-004",
            "contract_name": "Medical Diagnostic Summary",
            "contract_version_id": "cv-004-v1",
            "contract_version_number": 1,
            "status": "failed",
            "failed_checks": 1,
            "total_checks": 7,
            "duration_ms": 18.1,
            "review_status": "unreviewed",
            "created_at": "2026-10-19T22:45:00Z"
        },
        {
            "id": "run-019a8b2c-3d4e-7005",
            "contract_id": "c-001",
            "contract_name": "Customer Support Ticket Schema",
            "contract_version_id": "cv-001-v2",
            "contract_version_number": 2,
            "status": "passed",
            "failed_checks": 0,
            "total_checks": 6,
            "duration_ms": 11.4,
            "review_status": "reviewed",
            "created_at": "2026-10-19T22:30:00Z"
        }
    ]
}

MOCK_CONTRACTS = {
    "items": [
        {
            "id": "c-001",
            "name": "Customer Support Ticket Schema",
            "description": "Validates structured support inquiries, urgency levels, and user intent categorization.",
            "status": "active",
            "latest_version": 2,
            "total_versions": 2,
            "created_at": "2026-10-15T10:00:00Z",
            "updated_at": "2026-10-19T14:30:00Z"
        },
        {
            "id": "c-002",
            "name": "Financial Transaction Policy",
            "description": "Enforces strict numeric range checks, non-negative amounts, and required currency codes.",
            "status": "active",
            "latest_version": 1,
            "total_versions": 1,
            "created_at": "2026-10-16T12:00:00Z",
            "updated_at": "2026-10-16T12:00:00Z"
        },
        {
            "id": "c-003",
            "name": "Tool Call Policy & Param Allowlist",
            "description": "Deterministic safety gate ensuring model-invoked functions conform to permitted parameter types.",
            "status": "active",
            "latest_version": 3,
            "total_versions": 3,
            "created_at": "2026-10-17T09:00:00Z",
            "updated_at": "2026-10-19T18:00:00Z"
        },
        {
            "id": "c-004",
            "name": "Medical Diagnostic Summary",
            "description": "Structured schema validation for clinical notes, ICD-10 tags, and physician triage signoffs.",
            "status": "active",
            "latest_version": 1,
            "total_versions": 1,
            "created_at": "2026-10-18T16:00:00Z",
            "updated_at": "2026-10-18T16:00:00Z"
        }
    ],
    "total": 4,
    "limit": 50,
    "offset": 0
}

MOCK_CONTRACT_DETAIL = {
    "id": "c-001",
    "name": "Customer Support Ticket Schema",
    "description": "Validates structured support inquiries, urgency levels, and user intent categorization.",
    "status": "active",
    "created_at": "2026-10-15T10:00:00Z",
    "updated_at": "2026-10-19T14:30:00Z",
    "versions": [
        {
            "id": "cv-001-v2",
            "contract_id": "c-001",
            "version": 2,
            "definition_json": {
                "name": "Customer Support Ticket Schema",
                "checks": [
                    {"type": "required_fields", "field": "ticket_id", "severity": "critical"},
                    {"type": "required_fields", "field": "urgency", "severity": "error"},
                    {"type": "enum_values", "field": "urgency", "allowed_values": ["low", "medium", "high", "critical"], "severity": "error"},
                    {"type": "range_check", "field": "confidence", "min": 0.0, "max": 1.0, "severity": "warning"},
                    {"type": "disallowed_fields", "disallowed": ["raw_password", "credit_card"], "severity": "critical"}
                ]
            },
            "definition_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "created_at": "2026-10-19T14:30:00Z"
        },
        {
            "id": "cv-001-v1",
            "contract_id": "c-001",
            "version": 1,
            "definition_json": {
                "name": "Customer Support Ticket Schema",
                "checks": [
                    {"type": "required_fields", "field": "ticket_id", "severity": "critical"},
                    {"type": "required_fields", "field": "urgency", "severity": "error"},
                    {"type": "enum_values", "field": "urgency", "allowed_values": ["low", "high"], "severity": "error"}
                ]
            },
            "definition_hash": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
            "created_at": "2026-10-15T10:00:00Z"
        }
    ]
}

MOCK_RUNS = {
    "items": MOCK_OVERVIEW["recent_runs"],
    "total": 5,
    "limit": 50,
    "offset": 0
}

MOCK_RUN_DETAIL = {
    "id": "run-019a8b2c-3d4e-7002",
    "contract_id": "c-002",
    "contract_name": "Financial Transaction Policy",
    "contract_version_id": "cv-002-v1",
    "contract_version_number": 1,
    "status": "failed",
    "input_json": {
        "raw_prompt": "Transfer $500 from Account A to Account B",
        "user_id": "usr_99812"
    },
    "output_json": {
        "transaction_id": "tx_492019",
        "amount": -50.0,
        "currency": "XYZ",
        "recipient": "acc_002"
    },
    "result_json": {
        "status": "failed",
        "summary": {
            "total_checks": 8,
            "passed_checks": 6,
            "failed_checks": 2,
            "warnings_count": 0,
            "duration_ms": 22.8
        },
        "failures": [
            {
                "code": "OUT_OF_RANGE",
                "message": "Field 'amount' value -50.0 violates min constraint 0.01",
                "severity": "error",
                "path": "amount",
                "metadata": {"min": 0.01, "actual": -50.0},
                "suggested_repair": "Ensure amount is positive and greater than or equal to 0.01"
            },
            {
                "code": "INVALID_ENUM",
                "message": "Field 'currency' value 'XYZ' is not in allowed list: ['USD', 'EUR', 'GBP']",
                "severity": "error",
                "path": "currency",
                "metadata": {"allowed": ["USD", "EUR", "GBP"], "actual": "XYZ"},
                "suggested_repair": "Set currency to one of: USD, EUR, GBP"
            }
        ],
        "warnings": []
    },
    "duration_ms": 22.8,
    "aieval_version": "0.2.0",
    "created_at": "2026-10-19T23:10:00Z",
    "review": {
        "id": "rev-101",
        "run_id": "run-019a8b2c-3d4e-7002",
        "status": "unreviewed",
        "note": "Prompt injection attempt detected; negative amount bypassed frontend sanitizer.",
        "created_at": "2026-10-19T23:12:00Z",
        "updated_at": "2026-10-19T23:12:00Z"
    }
}

class MockHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST_DIR), **kwargs)

    def do_GET(self):
        url_path = self.path.split("?")[0]
        if url_path == "/api/v1/overview":
            self.send_json(MOCK_OVERVIEW)
        elif url_path == "/api/v1/contracts":
            self.send_json(MOCK_CONTRACTS)
        elif url_path.startswith("/api/v1/contracts/c-001"):
            self.send_json(MOCK_CONTRACT_DETAIL)
        elif url_path == "/api/v1/runs":
            self.send_json(MOCK_RUNS)
        elif url_path.startswith("/api/v1/runs/"):
            self.send_json(MOCK_RUN_DETAIL)
        elif url_path.startswith("/api/"):
            self.send_json({"detail": "Not found"}, status=404)
        else:
            # Check if static file exists, else fallback to index.html (SPA)
            req_path = DIST_DIR / url_path.lstrip("/")
            if not req_path.is_file():
                self.path = "/index.html"
            super().do_GET()

    def send_json(self, data, status=200):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    server = http.server.HTTPServer(("127.0.0.1", 8765), MockHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print("Mock server started on http://127.0.0.1:8765")
    time.sleep(1)

    chrome_bin = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if not os.path.exists(chrome_bin):
        print(f"Chrome not found at {chrome_bin}")
        sys.exit(1)

    targets = [
        ("overview.png", "http://127.0.0.1:8765/#overview"),
        ("contracts.png", "http://127.0.0.1:8765/#contracts"),
        ("contract_detail.png", "http://127.0.0.1:8765/#contracts/c-001"),
        ("workbench.png", "http://127.0.0.1:8765/#workbench"),
        ("runs.png", "http://127.0.0.1:8765/#runs"),
        ("run_detail.png", "http://127.0.0.1:8765/#runs/run-019a8b2c-3d4e-7002"),
    ]

    for fname, url in targets:
        out_path = SCREENSHOTS_DIR / fname
        cmd = [
            chrome_bin,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--user-data-dir=/tmp/chrome-headless-profile",
            f"--window-size=1440,900",
            f"--screenshot={out_path}",
            url
        ]
        print(f"Capturing {fname} from {url}...")
        subprocess.run(cmd, check=True)
        print(f"Saved {out_path}")

    server.shutdown()
    print("All screenshots captured successfully.")

if __name__ == "__main__":
    main()
