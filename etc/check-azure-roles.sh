#!/bin/bash
#
# Azure AI Foundry Role Check Script
# Checks if required RBAC roles are activated for using Azure AI Foundry
#
# Documentation:
#   https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/rbac-foundry
#   https://learn.microsoft.com/en-us/azure/role-based-access-control/check-access
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}✗ Azure CLI is not installed.${NC}"
    echo "  Install it from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    echo -e "${RED}✗ Not logged into Azure CLI.${NC}"
    echo "  Run: az login"
    exit 1
fi

# Get current user info
CURRENT_USER=$(az ad signed-in-user show --query userPrincipalName -o tsv 2>/dev/null || echo "")
CURRENT_USER_ID=$(az ad signed-in-user show --query id -o tsv 2>/dev/null || echo "")

# Get subscription info
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "                  Azure AI Foundry Role Check"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo -e "User:         ${BOLD}$CURRENT_USER${NC}"
echo -e "Subscription: ${BOLD}$SUBSCRIPTION_NAME${NC}"
echo ""

# Get subscription-level role assignments only
SUB_SCOPE="/subscriptions/$SUBSCRIPTION_ID"
SUB_ASSIGNMENTS=$(az role assignment list --assignee "$CURRENT_USER_ID" --scope "$SUB_SCOPE" --query "[?scope=='$SUB_SCOPE'].roleDefinitionName" -o tsv 2>/dev/null || echo "")

echo "───────────────────────────────────────────────────────────────────────────"
echo -e "${BOLD}Subscription-Level Role Assignments${NC}"
echo "───────────────────────────────────────────────────────────────────────────"
echo ""

HAS_SUFFICIENT_ACCESS=false
AI_ROLES_FOUND=()

if [ -n "$SUB_ASSIGNMENTS" ]; then
    while IFS= read -r role; do
        # Check if it's an AI-related or broad access role
        case "$role" in
            "Azure AI User"|"Azure AI Owner"|"Azure AI Account Owner"|"Azure AI Project Manager")
                echo -e "  ${GREEN}✓${NC} $role ${GREEN}(AI Foundry access)${NC}"
                AI_ROLES_FOUND+=("$role")
                HAS_SUFFICIENT_ACCESS=true
                ;;
            "Owner"|"Contributor")
                echo -e "  ${GREEN}✓${NC} $role ${GREEN}(full access - inherits to all resources)${NC}"
                AI_ROLES_FOUND+=("$role")
                HAS_SUFFICIENT_ACCESS=true
                ;;
            *)
                echo -e "  • $role"
                ;;
        esac
    done <<< "$SUB_ASSIGNMENTS"
else
    echo -e "  ${YELLOW}(No direct subscription-level roles)${NC}"
fi

echo ""

# Summary
if $HAS_SUFFICIENT_ACCESS; then
    echo -e "${GREEN}✓ SUFFICIENT ACCESS:${NC} You have subscription-level roles for Azure AI Foundry."
    echo "  These roles cascade to all resources below. No per-resource check needed."
else
    echo -e "${RED}✗ MISSING REQUIRED ROLES at subscription level.${NC}"
    echo ""
    echo "───────────────────────────────────────────────────────────────────────────"
    echo -e "${YELLOW}Share this with your Azure administrator:${NC}"
    echo "───────────────────────────────────────────────────────────────────────────"
    echo ""
    echo "  User:  $CURRENT_USER"
    echo "  Role:  Azure AI User (minimum)"
    echo "  Scope: /subscriptions/$SUBSCRIPTION_ID"
    echo ""
    echo "  Command for admin to run:"
    echo -e "  ${BLUE}az role assignment create --role \"Azure AI User\" --assignee \"$CURRENT_USER\" --scope /subscriptions/$SUBSCRIPTION_ID${NC}"
    echo ""
    echo "  Docs:  https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/rbac-foundry"
fi

echo ""
echo "───────────────────────────────────────────────────────────────────────────"
echo "Documentation"
echo "───────────────────────────────────────────────────────────────────────────"
echo ""
echo "  RBAC Guide:  https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/rbac-foundry"
echo "  Check Access: https://learn.microsoft.com/en-us/azure/role-based-access-control/check-access"
echo ""
