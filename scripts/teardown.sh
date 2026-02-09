#!/bin/bash
set -euo pipefail

# ── Config ──────────────────────────────────────────────
CONTAINER_RG="labelcheck-containers"

echo "=== LabelCheck Azure Teardown ==="
echo "This will delete the ENTIRE resource group: $CONTAINER_RG"
echo "  - Container Apps (frontend + backend)"
echo "  - Container Apps Environment"
echo "  - Container Registry (ACR)"
echo "  - Log Analytics workspace"
echo ""
echo "Your AI services in 'ttb-label-check' are NOT affected."
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo "── Deleting resource group $CONTAINER_RG (this takes a few minutes)..."
az group delete --name "$CONTAINER_RG" --yes --no-wait

echo ""
echo "=== Teardown Started ==="
echo "Deletion running in background. Check Azure portal to confirm."
echo "To redeploy: ./scripts/deploy.sh"
