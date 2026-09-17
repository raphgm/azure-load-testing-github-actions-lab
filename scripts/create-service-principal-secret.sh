#!/usr/bin/env bash
# Alternative to the OIDC path in the README, for teams that need
# azure/login@v1 compatibility or can't stand up federated credentials
# (e.g. an on-prem GitHub Enterprise runner without OIDC token support).
# This creates a real client-secret credential — treat the output as a
# secret, not a repo variable, and store it as AZURE_CREDENTIALS in
# GitHub's encrypted Actions secrets, never as a plain `vars.*`.
set -euo pipefail

APP_NAME="${1:-payments-api-loadtest-gha-secret}"
RESOURCE_GROUP="${2:-rg-payments-perf}"

SUBSCRIPTION_ID=$(az account show --query id -o tsv)

CREDENTIALS=$(az ad sp create-for-rbac \
  --name "$APP_NAME" \
  --role Contributor \
  --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" \
  --sdk-auth)

echo "$CREDENTIALS"
echo
echo "Store this JSON blob as a GitHub Actions secret (not a variable):"
echo "  gh secret set AZURE_CREDENTIALS --body '<paste the JSON above>'"
echo
echo "Then use azure/login@v1 in the workflow instead of azure/login@v2 with client-id/tenant-id/subscription-id:"
echo "  - uses: azure/login@v1"
echo "    with:"
echo "      creds: \${{ secrets.AZURE_CREDENTIALS }}"
