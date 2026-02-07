#!/bin/bash
# az-login.sh - Login to Azure and select subscription with filtering
# Usage: ./az-login.sh [filter]

FILTER="${1:-}"

# Check if already logged in
if ! az account show &>/dev/null; then
    echo "Opening browser for Azure login..."
    az login --only-show-errors
fi

echo ""
echo "=== Azure Subscriptions ==="

# Get subscriptions as JSON
SUBS_JSON=$(az account list --query "[].{name:name, id:id, isDefault:isDefault}" -o json 2>/dev/null)

if [ -z "$SUBS_JSON" ] || [ "$SUBS_JSON" = "[]" ]; then
    echo "No subscriptions found"
    exit 1
fi

# Filter and build arrays
NAMES=()
IDS=()
DEFAULTS=()

while IFS= read -r line; do
    name=$(echo "$line" | cut -d'|' -f1)
    id=$(echo "$line" | cut -d'|' -f2)
    isDefault=$(echo "$line" | cut -d'|' -f3)
    
    if [ -z "$FILTER" ] || echo "$name" | grep -qi "$FILTER"; then
        NAMES+=("$name")
        IDS+=("$id")
        DEFAULTS+=("$isDefault")
    fi
done < <(echo "$SUBS_JSON" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for item in data:
    print(f\"{item['name']}|{item['id']}|{item['isDefault']}\")
")

if [ ${#NAMES[@]} -eq 0 ]; then
    echo "No subscriptions matching '$FILTER'"
    exit 1
fi

# Display subscriptions
for i in "${!NAMES[@]}"; do
    marker=""
    if [ "${DEFAULTS[$i]}" = "true" ]; then
        marker=" (current)"
    fi
    echo "  $((i+1)). ${NAMES[$i]}$marker"
done

# Auto-select if only one match
if [ ${#NAMES[@]} -eq 1 ]; then
    echo ""
    echo "Auto-selecting: ${NAMES[0]}"
    az account set --subscription "${IDS[0]}"
    echo "Done! Subscription set."
    exit 0
fi

# Prompt for selection
echo ""
read -p "Select subscription (1-${#NAMES[@]}): " choice

if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#NAMES[@]} ]; then
    idx=$((choice-1))
    echo ""
    echo "Setting subscription: ${NAMES[$idx]}"
    az account set --subscription "${IDS[$idx]}"
    echo "Done!"
else
    echo "Invalid selection"
    exit 1
fi
