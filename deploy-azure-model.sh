#!/bin/bash
# Deploy a model to your Azure AI resource
# Usage: ./deploy-azure-model.sh [resource-filter] [model-filter]
# Examples:
#   ./deploy-azure-model.sh maeda           # Filter resources by 'maeda'
#   ./deploy-azure-model.sh maeda gpt-4o    # Filter resources and models

FILTER="${1:-}"
MODEL_FILTER="${2:-}"

echo "=== Azure AI Model Deployment ==="
echo

# Check if logged in
if ! az account show &>/dev/null; then
    echo "Not logged in. Run 'az login' first."
    exit 1
fi

echo "Current subscription: $(az account show --query name -o tsv)"
echo

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

# Show numbered list of resources
echo
echo "Available resources:"
echo "-----------------------------------------------------------"
NUM=0
while IFS=$'\t' read -r name rg loc; do
    NUM=$((NUM + 1))
    printf "[%2d] %-35s %-25s %s\n" "$NUM" "$name" "$rg" "$loc"
    eval "NAME_$NUM='$name'"
    eval "RG_$NUM='$rg'"
    eval "LOC_$NUM='$loc'"
done <<< "$RESOURCES"
echo

# Auto-select if only one, otherwise prompt
if [[ "$NUM" -eq 1 ]]; then
    SEL=1
    echo "Auto-selecting the only matching resource..."
else
    read -p "Select resource (1-$NUM): " SEL
    if [[ ! "$SEL" =~ ^[0-9]+$ ]] || [[ "$SEL" -lt 1 ]] || [[ "$SEL" -gt "$NUM" ]]; then
        echo "Invalid selection"
        exit 1
    fi
fi

eval "RESOURCE_NAME=\$NAME_$SEL"
eval "RESOURCE_GROUP=\$RG_$SEL"
eval "LOCATION=\$LOC_$SEL"

echo
echo "Resource: $RESOURCE_NAME"
echo "Location: $LOCATION"
echo

# Show currently deployed models
echo "=== Currently deployed models ==="
DEPLOYED_JSON=$(az cognitiveservices account deployment list \
    --name "$RESOURCE_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "[].{name:name, model:properties.model.name, version:properties.model.version}" \
    -o json 2>/dev/null)

DNUM=0
LETTERS="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
if [[ -n "$DEPLOYED_JSON" && "$DEPLOYED_JSON" != "[]" ]]; then
    echo "$DEPLOYED_JSON" | python3 -c "
import sys, json
data = json.load(sys.stdin)
letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
for i, item in enumerate(data):
    print(f\"  [{letters[i]}] {item['name']:<30} {item['model']:<20} {item['version']}\")
"
    DNUM=$(echo "$DEPLOYED_JSON" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
    
    # Store deployed model names
    for i in $(seq 0 $((DNUM - 1))); do
        dname=$(echo "$DEPLOYED_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)[$i]['name'])")
        eval "DEPLOYED_${LETTERS:$i:1}='$dname'"
    done
else
    echo "  (none)"
fi
echo

# List available OpenAI models for this region (only Standard/GlobalStandard SKUs)
echo "=== Available models to deploy (in $LOCATION) ==="
ALL_MODELS=$(az cognitiveservices model list -l "$LOCATION" \
    --query "[?kind=='OpenAI'].{name:model.name, version:model.version, skus:model.skus[].name}" -o json | \
    python3 -c "import sys,json; data=json.load(sys.stdin); [print(f\"{m['name']}\t{m['version']}\") for m in data if m.get('skus') and ('Standard' in m['skus'] or 'GlobalStandard' in m['skus'])]")

# Apply model filter if provided
if [[ -n "$MODEL_FILTER" ]]; then
    echo "Model filter: '$MODEL_FILTER'"
    MODELS=$(echo "$ALL_MODELS" | grep -i "$MODEL_FILTER")
    
    if [[ -z "$MODELS" ]]; then
        echo
        echo "No models found matching '$MODEL_FILTER'."
        echo "Available models:"
        echo "$ALL_MODELS" | head -50
        echo "... (use no filter to see all)"
        exit 1
    fi
else
    MODELS="$ALL_MODELS"
fi

if [[ -z "$MODELS" ]]; then
    echo "No OpenAI models available in $LOCATION"
    exit 1
fi

# Show numbered list of models
echo
MNUM=0
while IFS=$'\t' read -r mname mver; do
    MNUM=$((MNUM + 1))
    printf "[%3d] %-40s %s\n" "$MNUM" "$mname" "$mver"
    eval "MNAME_$MNUM='$mname'"
    eval "MVER_$MNUM='$mver'"
done <<< "$MODELS"

# Show hint about existing deployments
if [[ "$DNUM" -gt 0 ]]; then
    echo
    echo "Or enter A-${LETTERS:$((DNUM-1)):1} to use an existing deployment"
fi
echo

# Auto-select if only one model, otherwise prompt
if [[ "$MNUM" -eq 1 ]] && [[ "$DNUM" -eq 0 ]]; then
    MSEL=1
    echo "Auto-selecting the only matching model..."
else
    if [[ "$DNUM" -gt 0 ]]; then
        read -p "Select (1-$MNUM to deploy, A-${LETTERS:$((DNUM-1)):1} for existing): " MSEL
    else
        read -p "Select model to deploy (1-$MNUM): " MSEL
    fi
    
    # Check if user selected an existing deployment (letter)
    if [[ "$MSEL" =~ ^[A-Za-z]$ ]]; then
        MSEL_UPPER=$(echo "$MSEL" | tr 'a-z' 'A-Z')
        LETTER_IDX=$(echo "$LETTERS" | grep -bo "$MSEL_UPPER" | cut -d: -f1)
        
        if [[ -n "$LETTER_IDX" ]] && [[ "$LETTER_IDX" -lt "$DNUM" ]]; then
            eval "DEPLOYMENT_NAME=\$DEPLOYED_$MSEL_UPPER"
            
            # Get endpoint and API key
            ENDPOINT=$(az cognitiveservices account show -n "$RESOURCE_NAME" -g "$RESOURCE_GROUP" --query "properties.endpoint" -o tsv)
            API_KEY=$(az cognitiveservices account keys list -n "$RESOURCE_NAME" -g "$RESOURCE_GROUP" --query "key1" -o tsv)
            
            echo
            echo "=== Existing Deployment: $DEPLOYMENT_NAME ==="
            echo
            echo "ENDPOINT = \"$ENDPOINT\""
            echo "MODEL_DEPLOYMENT_NAME = \"$DEPLOYMENT_NAME\""
            echo "API_KEY = \"$API_KEY\""
            echo
            echo "Test with:"
            echo "  ./test-azure-model.sh $RESOURCE_NAME $DEPLOYMENT_NAME"
            exit 0
        else
            echo "Invalid selection"
            exit 1
        fi
    fi
    
    if [[ ! "$MSEL" =~ ^[0-9]+$ ]] || [[ "$MSEL" -lt 1 ]] || [[ "$MSEL" -gt "$MNUM" ]]; then
        echo "Invalid selection"
        exit 1
    fi
fi

eval "MODEL_NAME=\$MNAME_$MSEL"
eval "MODEL_VERSION=\$MVER_$MSEL"

# Get available SKUs for this model/version (only Standard/GlobalStandard)
SKUS=$(az cognitiveservices model list -l "$LOCATION" \
    --query "[?model.name=='$MODEL_NAME' && model.version=='$MODEL_VERSION'].model.skus[].name" -o tsv 2>/dev/null | grep -E "^(Standard|GlobalStandard)$" | sort -u)

if [[ -z "$SKUS" ]]; then
    echo "No Standard or GlobalStandard SKU available for this model."
    echo "This model may only support Provisioned deployments."
    exit 1
fi

# Check if GlobalStandard is available
HAS_GLOBAL=$(echo "$SKUS" | grep -c "GlobalStandard" || true)
HAS_STANDARD=$(echo "$SKUS" | grep -c "^Standard$" || true)

# Helper function to get available quota for a SKU
get_quota() {
    local sku=$1
    az cognitiveservices usage list --location "$LOCATION" \
        --query "[?contains(name.value, '$MODEL_NAME') && contains(name.value, '$sku')].{name:name.value, current:currentValue, limit:limit}" \
        -o json 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
for item in data:
    name = item['name']
    if any(x in name.lower() for x in ['finetune', 'batch', 'realtime', 'audio', 'transcribe', 'tts', 'diarize']):
        continue
    available = int(item['limit']) - int(item['current'])
    print(available)
    break
" 2>/dev/null
}

# Prioritize GlobalStandard
SKU_NAME=""
if [[ "$HAS_GLOBAL" -gt 0 ]]; then
    echo
    echo "=== Checking GlobalStandard quota for $MODEL_NAME in $LOCATION ==="
    GLOBAL_AVAIL=$(get_quota "GlobalStandard")
    
    if [[ -n "$GLOBAL_AVAIL" ]] && [[ "$GLOBAL_AVAIL" -gt 0 ]]; then
        echo "  ✓ GlobalStandard: ${GLOBAL_AVAIL}K TPM available"
        SKU_NAME="GlobalStandard"
    else
        echo "  ✗ GlobalStandard: No quota available"
        
        if [[ "$HAS_STANDARD" -gt 0 ]]; then
            STANDARD_AVAIL=$(get_quota "Standard")
            if [[ -n "$STANDARD_AVAIL" ]] && [[ "$STANDARD_AVAIL" -gt 0 ]]; then
                echo "  ✓ Standard: ${STANDARD_AVAIL}K TPM available"
                echo
                read -p "Deploy with Standard instead? (y/N): " USE_STANDARD
                if [[ "$USE_STANDARD" =~ ^[yY] ]]; then
                    SKU_NAME="Standard"
                else
                    echo "Cancelled."
                    exit 0
                fi
            else
                echo "  ✗ Standard: No quota available"
                echo
                echo "No quota available for any SKU. Try a different model or region."
                exit 1
            fi
        else
            echo
            echo "No quota available and Standard SKU not supported. Try a different model or region."
            exit 1
        fi
    fi
elif [[ "$HAS_STANDARD" -gt 0 ]]; then
    echo
    echo "=== Checking Standard quota for $MODEL_NAME in $LOCATION ==="
    STANDARD_AVAIL=$(get_quota "Standard")
    
    if [[ -n "$STANDARD_AVAIL" ]] && [[ "$STANDARD_AVAIL" -gt 0 ]]; then
        echo "  ✓ Standard: ${STANDARD_AVAIL}K TPM available"
        SKU_NAME="Standard"
    else
        echo "  ✗ Standard: No quota available"
        echo
        echo "No quota available. Try a different model or region."
        exit 1
    fi
fi

# Get deployment name (default to model name)
echo
read -p "Deployment name [$MODEL_NAME]: " DEPLOYMENT_NAME
DEPLOYMENT_NAME="${DEPLOYMENT_NAME:-$MODEL_NAME}"

# Get capacity (tokens per minute in thousands)
read -p "Capacity in 1K TPM [10]: " CAPACITY
CAPACITY="${CAPACITY:-10}"

echo
echo "=== Deploying ==="
echo "  Resource:    $RESOURCE_NAME"
echo "  Model:       $MODEL_NAME ($MODEL_VERSION)"
echo "  Deployment:  $DEPLOYMENT_NAME"
echo "  SKU:         $SKU_NAME"
echo "  Capacity:    ${CAPACITY}K TPM"
echo

read -p "Proceed? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[yY] ]]; then
    echo "Cancelled."
    exit 0
fi

echo
echo "Creating deployment..."
az cognitiveservices account deployment create \
    --name "$RESOURCE_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --deployment-name "$DEPLOYMENT_NAME" \
    --model-name "$MODEL_NAME" \
    --model-version "$MODEL_VERSION" \
    --model-format "OpenAI" \
    --sku-name "$SKU_NAME" \
    --sku-capacity "$CAPACITY"

if [[ $? -eq 0 ]]; then
    # Get endpoint and API key
    ENDPOINT=$(az cognitiveservices account show -n "$RESOURCE_NAME" -g "$RESOURCE_GROUP" --query "properties.endpoint" -o tsv)
    API_KEY=$(az cognitiveservices account keys list -n "$RESOURCE_NAME" -g "$RESOURCE_GROUP" --query "key1" -o tsv)
    
    echo
    echo "=== Success! ==="
    echo
    echo "ENDPOINT = \"$ENDPOINT\""
    echo "MODEL_DEPLOYMENT_NAME = \"$DEPLOYMENT_NAME\""
    echo "API_KEY = \"$API_KEY\""
    echo
    echo "Test with:"
    echo "  ./test-azure-model.sh $RESOURCE_NAME $DEPLOYMENT_NAME"
else
    echo
    echo "Deployment failed. Check the error above."
fi
