#!/bin/bash
# Get API key for an Azure AI resource
# Usage: ./get-azure-key.sh [filter]
# Examples:
#   ./get-azure-key.sh maedaoct25

FILTER="${1:-}"

# Check if logged in
if ! az account show &>/dev/null; then
    echo "Not logged in. Run 'az login' first."
    exit 1
fi

# Get resources (with optional filter)
if [[ -n "$FILTER" ]]; then
    RESOURCES=$(az resource list --resource-type "Microsoft.CognitiveServices/accounts" \
        --query "[].{name:name, rg:resourceGroup, loc:location}" -o tsv | grep -i "$FILTER")
else
    RESOURCES=$(az resource list --resource-type "Microsoft.CognitiveServices/accounts" \
        --query "[].{name:name, rg:resourceGroup, loc:location}" -o tsv)
fi

if [[ -z "$RESOURCES" ]]; then
    echo "No resources found${FILTER:+ matching '$FILTER'}." >&2
    exit 1
fi

# Count and select resource
NUM=0
while IFS=$'\t' read -r name rg loc; do
    NUM=$((NUM + 1))
    eval "NAME_$NUM='$name'"
    eval "RG_$NUM='$rg'"
done <<< "$RESOURCES"

if [[ "$NUM" -eq 1 ]]; then
    RESOURCE_NAME="$NAME_1"
    RESOURCE_GROUP="$RG_1"
else
    echo "Resources:" >&2
    i=0
    while IFS=$'\t' read -r name rg loc; do
        i=$((i + 1))
        printf "[%2d] %s (%s)\n" "$i" "$name" "$rg" >&2
    done <<< "$RESOURCES"
    read -p "Select (1-$NUM): " SEL
    eval "RESOURCE_NAME=\$NAME_$SEL"
    eval "RESOURCE_GROUP=\$RG_$SEL"
fi

# Get endpoint and key
ENDPOINT=$(az cognitiveservices account show -n "$RESOURCE_NAME" -g "$RESOURCE_GROUP" --query "properties.endpoint" -o tsv)
API_KEY=$(az cognitiveservices account keys list -n "$RESOURCE_NAME" -g "$RESOURCE_GROUP" --query "key1" -o tsv)

echo "RESOURCE_NAME=$RESOURCE_NAME"
echo "RESOURCE_GROUP=$RESOURCE_GROUP"
echo "ENDPOINT=$ENDPOINT"
echo "API_KEY=$API_KEY"
