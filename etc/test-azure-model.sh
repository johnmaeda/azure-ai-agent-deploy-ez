#!/bin/bash
# Test an Azure AI model deployment
# Usage: ./test-azure-model.sh [resource-filter] [model-name]
# Examples:
#   ./test-azure-model.sh maedaoct25 gpt-4o-mini

FILTER="${1:-}"
MODEL_NAME="${2:-}"

echo "=== Azure AI Model Test ==="
echo

# Check if logged in
if ! az account show &>/dev/null; then
    echo "Not logged in. Run 'az login' first."
    exit 1
fi

echo "Current subscription: $(az account show --query name -o tsv)"
echo

# Get resources (with optional filter)
if [[ -n "$FILTER" ]]; then
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
    echo "Resources:"
    i=0
    while IFS=$'\t' read -r name rg loc; do
        i=$((i + 1))
        printf "[%2d] %s (%s)\n" "$i" "$name" "$rg"
    done <<< "$RESOURCES"
    read -p "Select (1-$NUM): " SEL
    eval "RESOURCE_NAME=\$NAME_$SEL"
    eval "RESOURCE_GROUP=\$RG_$SEL"
fi

echo "Resource: $RESOURCE_NAME"

# Get endpoint and key
ENDPOINT=$(az cognitiveservices account show -n "$RESOURCE_NAME" -g "$RESOURCE_GROUP" --query "properties.endpoint" -o tsv)
API_KEY=$(az cognitiveservices account keys list -n "$RESOURCE_NAME" -g "$RESOURCE_GROUP" --query "key1" -o tsv)

echo "Endpoint: $ENDPOINT"
echo

# List deployed models if no model specified
if [[ -z "$MODEL_NAME" ]]; then
    echo "Deployed models:"
    az cognitiveservices account deployment list -n "$RESOURCE_NAME" -g "$RESOURCE_GROUP" \
        --query "[].{name:name, model:properties.model.name}" -o table
    echo
    read -p "Enter deployment name to test: " MODEL_NAME
fi

echo
echo "Testing deployment: $MODEL_NAME"
echo "---"

# Test with curl
curl -s "${ENDPOINT}openai/deployments/${MODEL_NAME}/chat/completions?api-version=2024-10-21" \
  -H "Content-Type: application/json" \
  -H "api-key: $API_KEY" \
  -d '{
    "messages": [{"role": "user", "content": "Say hello in one word"}],
    "max_tokens": 10
  }' | python3 -c "import sys,json; r=json.load(sys.stdin); print(r.get('choices',[{}])[0].get('message',{}).get('content', r))"

echo
echo "---"
echo "Test complete!"
