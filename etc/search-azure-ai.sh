#!/bin/bash
# Search for Azure AI Foundry resources by name
# Usage: ./search-azure-ai.sh [filter]

set -e

SEARCH_TERM="${1:-}"

if [[ -z "$SEARCH_TERM" ]]; then
    echo "=== All Azure AI Resources ==="
else
    echo "=== Searching Azure AI resources for '$SEARCH_TERM' ==="
fi
echo

# Check if logged in
if ! az account show &>/dev/null; then
    echo "Not logged in. Run 'az login' first."
    exit 1
fi

# Show current subscription
echo "Subscription: $(az account show --query name -o tsv)"
echo

# Search AI resources (accounts)
echo "=== AI Resources ==="
if [[ -z "$SEARCH_TERM" ]]; then
    az resource list --resource-type "Microsoft.CognitiveServices/accounts" \
        --query "[].{resourceName:name, resourceGroup:resourceGroup, location:location}" -o table
else
    az resource list --resource-type "Microsoft.CognitiveServices/accounts" \
        --query "[?contains(name, '$SEARCH_TERM') || contains(resourceGroup, '$SEARCH_TERM')].{resourceName:name, resourceGroup:resourceGroup, location:location}" -o table
fi

echo
echo "=== AI Foundry Projects ==="
if [[ -z "$SEARCH_TERM" ]]; then
    az resource list --resource-type "Microsoft.CognitiveServices/accounts/projects" \
        --query "[].{fullName:name, resourceGroup:resourceGroup, location:location}" -o table 2>/dev/null || echo "(none found)"
else
    az resource list --resource-type "Microsoft.CognitiveServices/accounts/projects" \
        --query "[?contains(name, '$SEARCH_TERM') || contains(resourceGroup, '$SEARCH_TERM')].{fullName:name, resourceGroup:resourceGroup, location:location}" -o table 2>/dev/null || echo "(none found)"
fi

# Show endpoint format
echo
echo "=== Project Endpoints ==="
if [[ -z "$SEARCH_TERM" ]]; then
    az resource list --resource-type "Microsoft.CognitiveServices/accounts/projects" \
        --query "[].name" -o tsv 2>/dev/null | while read -r fullname; do
        RESOURCE=$(echo "$fullname" | cut -d'/' -f1)
        PROJECT=$(echo "$fullname" | cut -d'/' -f2)
        echo "https://${RESOURCE}.services.ai.azure.com/api/projects/${PROJECT}"
    done
else
    az resource list --resource-type "Microsoft.CognitiveServices/accounts/projects" \
        --query "[?contains(name, '$SEARCH_TERM') || contains(resourceGroup, '$SEARCH_TERM')].name" -o tsv 2>/dev/null | while read -r fullname; do
        RESOURCE=$(echo "$fullname" | cut -d'/' -f1)
        PROJECT=$(echo "$fullname" | cut -d'/' -f2)
        echo "https://${RESOURCE}.services.ai.azure.com/api/projects/${PROJECT}"
    done
fi
