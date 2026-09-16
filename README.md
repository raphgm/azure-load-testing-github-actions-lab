# Automate Azure Load Testing Using GitHub Actions

A production-shaped lab that wires **Azure Load Testing** into a **GitHub Actions** pipeline so every pull request gets an automated, pass/fail-gated performance test — authenticated via Microsoft Entra Workload ID federation (OIDC), with zero stored secrets.

Companion lab for the article [Automate Azure Load Testing Using GitHub Actions](https://raphaelgmomoh.pages.dev/articles/automate-azure-load-testing-github-actions), built on the pattern in Microsoft's [Automate Azure Load Testing by using GitHub Actions](https://learn.microsoft.com/en-us/credentials/applied-skills/automate-azure-load-testing-by-using-github-actions/) Applied Skills path.

---

## Architecture

```mermaid
flowchart TD
    PR["Pull Request opened"] --> GHA["GitHub Actions workflow triggers"]
    GHA --> OIDC["Azure login via OIDC\n(Microsoft Entra Workload ID)"]
    OIDC --> ALT["Azure Load Testing\nruns the configured test"]
    ALT --> Target["Target: Azure Container Apps\n(system under test)"]
    ALT --> Criteria{"Pass/Fail Criteria\nmet?"}
    Criteria -- "Yes" --> Pass["✅ Check passes — PR can merge"]
    Criteria -- "No" --> Fail["❌ Check fails — PR blocked"]
    Fail --> AppInsights["Application Insights\ncorrelated server-side trace"]
```

---

## Repository Structure

```text
.
├── README.md
├── .github/
│   └── workflows/
│       └── load-test.yml          # PR-triggered load test workflow (OIDC auth)
├── loadtest-config.yaml           # URL-based test definition + pass/fail criteria
└── src/
    ├── bicep/
    │   └── main.bicep             # Provisions the Azure Load Testing resource + RBAC
    └── python/
        ├── check_run.py           # Standalone script to poll a test run's pass/fail state
        └── requirements.txt
```

---

## Quick Start

### 1. Provision the Azure Load Testing resource (Bicep)

```bash
az deployment group create \
  --resource-group rg-payments-perf \
  --template-file src/bicep/main.bicep \
  --parameters loadTestName=payments-api-loadtest principalId=<your-service-principal-object-id>
```

### 2. Configure OIDC federation + repo variables

See the [article](https://raphaelgmomoh.pages.dev/articles/automate-azure-load-testing-github-actions) for the full `az ad app` / `gh variable set` walkthrough — summarized:

```bash
az ad app create --display-name "payments-api-loadtest-gha"
export APP_ID=$(az ad app list --display-name "payments-api-loadtest-gha" --query "[0].appId" -o tsv)
az ad sp create --id "$APP_ID"

az ad app federated-credential create --id "$APP_ID" --parameters '{
  "name": "github-actions-pr",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:YOUR_ORG/YOUR_REPO:pull_request",
  "audiences": ["api://AzureADTokenExchange"]
}'

gh variable set AZURE_CLIENT_ID --body "$APP_ID"
gh variable set AZURE_TENANT_ID --body "$(az account show --query tenantId -o tsv)"
gh variable set AZURE_SUBSCRIPTION_ID --body "$(az account show --query id -o tsv)"
```

### 3. Open a pull request

The workflow in `.github/workflows/load-test.yml` runs automatically and posts a pass/fail check against the thresholds in `loadtest-config.yaml`.

### 4. (Optional) Check a run's result locally

```bash
cd src/python
pip install -r requirements.txt
python check_run.py --test-id payments-api-pr-check
```

---

## License

MIT — use it, fork it, adapt it to your own pipeline.
