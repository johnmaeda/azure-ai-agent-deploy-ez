#!/bin/bash
# List available Azure AI models in your subscription
# Usage: ./list-azure-models.sh [filter] [resource-name] [resource-group]
# Examples:
#   ./list-azure-models.sh                        # Interactive, shows all
#   ./list-azure-models.sh maeda                  # Interactive, filtered
#   ./list-azure-models.sh "" myresource myrg    # Direct mode

FILTER="${1:-}"
RESOURCE_NAME="${2:-}"
RESOURCE_GROUP="${3:-}"

echo "=== Azure AI Model Discovery ==="
echo

# Check if logged in
if ! az account show &>/dev/null; then
    echo "Not logged in. Run 'az login' first."
    exit 1
fi

# Show current subscription
echo "Current subscription: $(az account show --query name -o tsv)"
echo

# If resource name and group provided directly, list models
if [[ -n "$RESOURCE_NAME" && -n "$RESOURCE_GROUP" ]]; then
    echo "=== Deployed models in '$RESOURCE_NAME' ==="
    DEPLOYMENTS=$(az cognitiveservices account deployment list \
        --name "$RESOURCE_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "[].{deploymentName:name, model:properties.model.name, version:properties.model.version}" \
        -o table 2>/dev/null)
    
    if [[ -z "$DEPLOYMENTS" ]] || [[ $(echo "$DEPLOYMENTS" | wc -l) -le 2 ]]; then
        echo "(No models deployed)"
        echo
        echo "Deploy a model with: ./deploy-azure-model.sh $RESOURCE_NAME"
    else
        echo "$DEPLOYMENTS"
        echo
        echo "MODEL_DEPLOYMENT_NAME = \"<deploymentName>\""
    fi
    exit 0
fi

# Get resources (with optional filter)
echo "Fetching resources..."
if [[ -n "$FILTER" ]]; then
    echo "Filter: '$FILTER'"
    RESOURCES=$(az resource list --resource-type "Microsoft.CognitiveServices/accounts" \
        --query "[].{name:name, rg:resourceGroup, loc:location}" -o tsv | grep -i "$FILTER")
else
    RESOURCES=$(az resource list --resource-type "Microsoft.CognitiveServices/accounts" \
        --query "[].{name:name, rg:resourceGroup, loc:location}" -o tsv)
fi

if [[ -z "$RESOURCES" ]]; then
    echo "No resources found${FILTER:+ matching '$FILTER'}."
    exit 1
fi

# Show numbered list
echo
echo "Available resources:"
echo "-----------------------------------------------------------"
NUM=0
while IFS=$'\t' read -r name rg loc; do
    NUM=$((NUM + 1))
    printf "[%2d] %-35s %-25s %s\n" "$NUM" "$name" "$rg" "$loc"
    eval "NAME_$NUM='$name'"
    eval "RG_$NUM='$rg'"
done <<< "$RESOURCES"
echo

# Auto-select if only one, otherwise prompt
if [[ "$NUM" -eq 1 ]]; then
    SEL=1
    echo "Auto-selecting the only matching resource..."
else
    read -p "Select (1-$NUM): " SEL

    if [[ ! "$SEL" =~ ^[0-9]+$ ]] || [[ "$SEL" -lt 1 ]] || [[ "$SEL" -gt "$NUM" ]]; then
        echo "Invalid selection"
        exit 1
    fi
fi

eval "RESOURCE_NAME=\$NAME_$SEL"
eval "RESOURCE_GROUP=\$RG_$SEL"

echo
echo "=== Deployed models in '$RESOURCE_NAME' ==="
DEPLOYMENTS=$(az cognitiveservices account deployment list \
    --name "$RESOURCE_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "[].{deploymentName:name, model:properties.model.name, version:properties.model.version}" \
    -o table 2>/dev/null)

if [[ -z "$DEPLOYMENTS" ]] || [[ $(echo "$DEPLOYMENTS" | wc -l) -le 2 ]]; then
    echo "(No models deployed)"
    echo
    echo "Deploy a model with: ./deploy-azure-model.sh $RESOURCE_NAME"
else
    echo "$DEPLOYMENTS"
    echo
    echo "MODEL_DEPLOYMENT_NAME = \"<deploymentName>\""
fi
