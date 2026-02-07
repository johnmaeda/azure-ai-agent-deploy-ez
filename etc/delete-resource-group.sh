#!/bin/bash
# delete-resource-group.sh - Delete Azure resource group with search/filter
# Usage: ./delete-resource-group.sh [filter]

FILTER="${1:-}"

echo "=== Delete Azure Resource Group ==="
echo

# Check if logged in
if ! az account show &>/dev/null; then
    echo "Not logged in. Run 'az login' first."
    exit 1
fi

echo "Subscription: $(az account show --query name -o tsv)"
echo

# Get resource groups
if [[ -n "$FILTER" ]]; then
    echo "Searching for resource groups matching '$FILTER'..."
    RGS=$(az group list --query "[?contains(name, '$FILTER')].{name:name, location:location}" -o tsv)
else
    echo "Listing all resource groups..."
    RGS=$(az group list --query "[].{name:name, location:location}" -o tsv)
fi

if [[ -z "$RGS" ]]; then
    echo "No resource groups found${FILTER:+ matching '$FILTER'}."
    exit 1
fi

# Show numbered list
echo
echo "Resource groups:"
echo "-----------------------------------------------------------"
NUM=0
while IFS=$'\t' read -r name loc; do
    NUM=$((NUM + 1))
    printf "[%2d] %-45s %s\n" "$NUM" "$name" "$loc"
    eval "RG_$NUM='$name'"
done <<< "$RGS"
echo

if [[ "$NUM" -eq 0 ]]; then
    echo "No resource groups found."
    exit 1
fi

# Auto-select if only one
if [[ "$NUM" -eq 1 ]]; then
    SEL=1
    echo "Only one match found."
else
    read -p "Select resource group to delete (1-$NUM): " SEL
    if [[ ! "$SEL" =~ ^[0-9]+$ ]] || [[ "$SEL" -lt 1 ]] || [[ "$SEL" -gt "$NUM" ]]; then
        echo "Invalid selection"
        exit 1
    fi
fi

eval "RG_NAME=\$RG_$SEL"

echo
echo "⚠️  WARNING: This will permanently delete:"
echo "   Resource Group: $RG_NAME"
echo "   And ALL resources inside it!"
echo
read -p "Type the resource group name to confirm: " CONFIRM

if [[ "$CONFIRM" != "$RG_NAME" ]]; then
    echo "Name doesn't match. Cancelled."
    exit 0
fi

echo
echo "Deleting resource group '$RG_NAME'..."
az group delete -n "$RG_NAME" --yes --no-wait

echo "Deletion started (running in background)."
echo "Check status: az group show -n $RG_NAME -o table"
