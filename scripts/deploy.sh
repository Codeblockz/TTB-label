#!/bin/bash
set -euo pipefail

# ── Config ──────────────────────────────────────────────
# AI services live in ttb-label-check (not touched by deploy/teardown)
# Container infra gets its own resource group for easy cleanup
CONTAINER_RG="labelcheck-containers"
LOCATION="eastus"
ACR_NAME="labelcheckacr"
ENVIRONMENT="labelcheck-env"
BACKEND_APP="backend"
FRONTEND_APP="frontend"

# ── Load secrets from .env ──────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: .env file not found at $ENV_FILE"
    exit 1
fi

# Source env vars (skip comments and blank lines)
set -a
while IFS= read -r line; do
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    eval "$line"
done < "$ENV_FILE"
set +a

echo "=== LabelCheck Azure Deploy ==="
echo "Container RG: $CONTAINER_RG"
echo "ACR:          $ACR_NAME"
echo ""

# ── Step 1: Create resource group + ACR if needed ───────
if ! az group show --name "$CONTAINER_RG" &>/dev/null; then
    echo "── Creating resource group $CONTAINER_RG..."
    az group create --name "$CONTAINER_RG" --location "$LOCATION" --only-show-errors
fi

if ! az acr show --name "$ACR_NAME" &>/dev/null; then
    echo "── Creating container registry $ACR_NAME..."
    az acr create --resource-group "$CONTAINER_RG" --name "$ACR_NAME" --sku Basic --admin-enabled true --only-show-errors
fi

# ── Step 2: Build and push images ───────────────────────
echo "── Building backend image..."
az acr build \
    --registry "$ACR_NAME" \
    --image labelcheck-backend:latest \
    --file "$PROJECT_ROOT/backend/Dockerfile" \
    "$PROJECT_ROOT/backend/" \
    --only-show-errors

echo "── Building frontend image..."
az acr build \
    --registry "$ACR_NAME" \
    --image labelcheck-frontend:latest \
    --file "$PROJECT_ROOT/frontend/Dockerfile" \
    "$PROJECT_ROOT/frontend/" \
    --only-show-errors

# ── Step 3: Create Container Apps Environment ───────────
echo "── Creating Container Apps environment..."
az containerapp env create \
    --name "$ENVIRONMENT" \
    --resource-group "$CONTAINER_RG" \
    --location "$LOCATION" \
    --only-show-errors

# ── Step 4: Deploy backend (internal) ───────────────────
echo "── Deploying backend..."
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)

az containerapp create \
    --name "$BACKEND_APP" \
    --resource-group "$CONTAINER_RG" \
    --environment "$ENVIRONMENT" \
    --image "$ACR_NAME.azurecr.io/labelcheck-backend:latest" \
    --registry-server "$ACR_NAME.azurecr.io" \
    --registry-username "$ACR_NAME" \
    --registry-password "$ACR_PASSWORD" \
    --target-port 8000 \
    --ingress internal \
    --transport http \
    --allow-insecure true \
    --min-replicas 0 \
    --max-replicas 3 \
    --cpu 1.0 \
    --memory 2.0Gi \
    --env-vars \
        AZURE_VISION_ENDPOINT="$AZURE_VISION_ENDPOINT" \
        AZURE_VISION_KEY="$AZURE_VISION_KEY" \
        AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
        AZURE_OPENAI_KEY="$AZURE_OPENAI_KEY" \
        AZURE_OPENAI_DEPLOYMENT="${AZURE_OPENAI_DEPLOYMENT:-gpt-4o-mini}" \
        AZURE_OPENAI_API_VERSION="${AZURE_OPENAI_API_VERSION:-2024-12-01-preview}" \
        DATABASE_URL="sqlite+aiosqlite:///./data/labelcheck.db" \
        UPLOAD_DIR="./uploads" \
        LOG_LEVEL="info" \
    --only-show-errors

# ── Step 5: Get backend FQDN ───────────────────────────
BACKEND_FQDN=$(az containerapp show \
    --name "$BACKEND_APP" \
    --resource-group "$CONTAINER_RG" \
    --query "properties.configuration.ingress.fqdn" -o tsv)

echo "── Backend FQDN: $BACKEND_FQDN"

# ── Step 6: Deploy frontend (external) ──────────────────
echo "── Deploying frontend..."
az containerapp create \
    --name "$FRONTEND_APP" \
    --resource-group "$CONTAINER_RG" \
    --environment "$ENVIRONMENT" \
    --image "$ACR_NAME.azurecr.io/labelcheck-frontend:latest" \
    --registry-server "$ACR_NAME.azurecr.io" \
    --registry-username "$ACR_NAME" \
    --registry-password "$ACR_PASSWORD" \
    --target-port 80 \
    --ingress external \
    --min-replicas 0 \
    --max-replicas 3 \
    --cpu 0.5 \
    --memory 1.0Gi \
    --env-vars \
        BACKEND_URL="http://$BACKEND_FQDN" \
    --only-show-errors

# ── Step 7: Print the URL ──────────────────────────────
FRONTEND_FQDN=$(az containerapp show \
    --name "$FRONTEND_APP" \
    --resource-group "$CONTAINER_RG" \
    --query "properties.configuration.ingress.fqdn" -o tsv)

echo ""
echo "=== Deploy Complete ==="
echo "App URL: https://$FRONTEND_FQDN"
echo ""
echo "To tear down: ./scripts/teardown.sh"
