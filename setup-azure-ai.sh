#!/bin/bash
# setup-azure-ai.sh - Create Azure AI Foundry resource and project from scratch
# Usage: ./setup-azure-ai.sh [name-prefix] [location]
# Example: ./setup-azure-ai.sh myproject swedencentral

set -e

PREFIX="${1:-myai}"
LOCATION="${2:-}"

echo "=== Azure AI Foundry Setup ==="
echo

# Check if logged in
if ! az account show &>/dev/null; then
    echo "Not logged in. Run './az-login.sh' first."
    exit 1
fi

SUB_NAME=$(az account show --query name -o tsv)
SUB_ID=$(az account show --query id -o tsv)
echo "Subscription: $SUB_NAME"
echo

# Show available locations for AIServices
if [[ -z "$LOCATION" ]]; then
    echo "=== Available locations for AI Services ==="
    echo "Recommended: swedencentral, eastus2, eastus, westus3"
    echo
    read -p "Enter location [swedencentral]: " LOCATION
    LOCATION="${LOCATION:-swedencentral}"
fi

# Generate names
RESOURCE_GROUP="rg-${PREFIX}"
RESOURCE_NAME="${PREFIX}-resource"
PROJECT_NAME="${PREFIX}-project"

echo
echo "=== Configuration ==="
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Resource Name:  $RESOURCE_NAME"
echo "  Project Name:   $PROJECT_NAME"
echo "  Location:       $LOCATION"
echo

read -p "Proceed? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[yY] ]]; then
    echo "Cancelled."
    exit 0
fi

# Step 1: Create resource group
echo
echo "=== Step 1: Creating resource group ==="
if az group show -n "$RESOURCE_GROUP" &>/dev/null; then
    echo "Resource group '$RESOURCE_GROUP' already exists"
else
    az group create -n "$RESOURCE_GROUP" -l "$LOCATION" -o none
    echo "Created resource group: $RESOURCE_GROUP"
fi

# Step 2: Create AI Services resource with project management enabled
echo
echo "=== Step 2: Creating AI Services resource ==="
if az cognitiveservices account show -n "$RESOURCE_NAME" -g "$RESOURCE_GROUP" &>/dev/null; then
    echo "Resource '$RESOURCE_NAME' already exists"
    # Enable project management if not already enabled
    echo "Enabling project management..."
    az rest --method PATCH \
        --url "https://management.azure.com/subscriptions/${SUB_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.CognitiveServices/accounts/${RESOURCE_NAME}?api-version=2025-06-01" \
        --body '{"properties":{"allowProjectManagement":true}}' \
        -o none 2>/dev/null || echo "(may already be enabled)"
else
    # Create resource via REST API to include allowProjectManagement and customSubDomainName
    az rest --method PUT \
        --url "https://management.azure.com/subscriptions/${SUB_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.CognitiveServices/accounts/${RESOURCE_NAME}?api-version=2025-06-01" \
        --body "{
            \"location\": \"${LOCATION}\",
            \"kind\": \"AIServices\",
            \"sku\": {\"name\": \"S0\"},
            \"identity\": {\"type\": \"SystemAssigned\"},
            \"properties\": {
                \"allowProjectManagement\": true,
                \"publicNetworkAccess\": \"Enabled\",
                \"customSubDomainName\": \"${RESOURCE_NAME}\"
            }
        }" \
        -o none
    echo "Created AI Services resource: $RESOURCE_NAME"
fi

# Wait for resource to be ready
echo "Waiting for resource to be ready..."
sleep 5

# Step 3: Create project via REST API
echo
echo "=== Step 3: Creating AI Foundry project ==="

# Check if project already exists
EXISTING=$(az rest --method GET \
    --url "https://management.azure.com/subscriptions/${SUB_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.CognitiveServices/accounts/${RESOURCE_NAME}/projects?api-version=2025-06-01" \
    --query "value[?name=='${RESOURCE_NAME}/${PROJECT_NAME}']" -o tsv 2>/dev/null || echo "")

if [[ -n "$EXISTING" ]]; then
    echo "Project '$PROJECT_NAME' already exists"
else
    # Create project via REST
    az rest --method PUT \
        --url "https://management.azure.com/subscriptions/${SUB_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.CognitiveServices/accounts/${RESOURCE_NAME}/projects/${PROJECT_NAME}?api-version=2025-06-01" \
        --body "{
            \"location\": \"${LOCATION}\",
            \"kind\": \"AIServices\",
            \"identity\": {
                \"type\": \"SystemAssigned\"
            },
            \"properties\": {
                \"displayName\": \"${PROJECT_NAME}\",
                \"description\": \"Created via CLI\"
            }
        }" \
        -o none 2>&1 && echo "Created project: $PROJECT_NAME" || echo "Project creation may have failed - check manually"
fi

# Get endpoint info
echo
echo "=== Setup Complete ==="
ENDPOINT="https://${RESOURCE_NAME}.services.ai.azure.com/api/projects/${PROJECT_NAME}"
API_KEY=$(az cognitiveservices account keys list -n "$RESOURCE_NAME" -g "$RESOURCE_GROUP" --query "key1" -o tsv 2>/dev/null || echo "<key-unavailable>")

echo
echo "PROJECT_ENDPOINT = \"$ENDPOINT\""
echo "API_KEY = \"$API_KEY\""
echo
echo "Next steps:"
echo "  1. Deploy a model:  ./deploy-azure-model.sh $RESOURCE_NAME"
echo "  2. Test the model:  ./test-azure-model.sh $RESOURCE_NAME <deployment-name>"
echo "  3. Run the agent:   Update agent.py with the endpoint above"
