#!/usr/bin/env python3
"""
Standalone verification script: polls an Azure Load Testing test run's status
via the data-plane REST API and prints a pass/fail summary.

Uses DefaultAzureCredential, so it works locally (az login), in a pipeline
(OIDC/managed identity), or with a service principal — no code changes needed
across environments.

Usage:
    python check_run.py --test-id payments-api-pr-check \
        --data-plane-uri <load-test-resource>.<region>.cnt-prod.loadtesting.azure.com
"""

import argparse
import sys
import time

import requests
from azure.identity import DefaultAzureCredential

API_VERSION = "2023-04-01-preview"
SCOPE = "https://cnt-prod.loadtesting.azure.com/.default"


def get_latest_test_run(data_plane_uri: str, test_id: str, token: str) -> dict:
    url = f"https://{data_plane_uri}/test-runs?testId={test_id}&api-version={API_VERSION}"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    resp.raise_for_status()
    runs = resp.json().get("value", [])
    if not runs:
        raise SystemExit(f"No test runs found for testId={test_id}")
    return sorted(runs, key=lambda r: r["startDateTime"], reverse=True)[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-id", required=True)
    parser.add_argument("--data-plane-uri", required=True)
    parser.add_argument("--poll-interval", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    credential = DefaultAzureCredential()
    token = credential.get_token(SCOPE).token

    elapsed = 0
    while elapsed < args.timeout:
        run = get_latest_test_run(args.data_plane_uri, args.test_id, token)
        status = run.get("status")
        print(f"[{elapsed}s] test run {run['testRunId']} status={status}")

        if status in ("DONE", "FAILED", "CANCELLED"):
            result = run.get("testResult", "UNKNOWN")
            print(f"\nFinal result: {result}")
            for criterion, outcome in run.get("testArtifacts", {}).get(
                "outputArtifacts", {}
            ).items():
                print(f"  {criterion}: {outcome}")
            return 0 if result == "PASSED" else 1

        time.sleep(args.poll_interval)
        elapsed += args.poll_interval

    print("Timed out waiting for test run to complete.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
