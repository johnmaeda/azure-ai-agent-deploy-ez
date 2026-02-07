# Troubleshooting Guide

This document covers common issues when deploying Azure AI agents and their solutions.

## Authentication Issues

### "Not logged in to Azure CLI"

**Problem:** User hasn't authenticated with Azure CLI.

**Solution:**
```bash
# Browser-based login (easiest)
az login

# Device code login (for remote/SSH sessions)
az login --use-device-code
```

### "Tenant Mismatch" or "Token audience validation failed"

**Problem:** User logged into wrong Azure AD tenant, or resource is in different tenant.

**Symptoms:**
- Error: `AADSTS700016: Application with identifier 'https://cognitiveservices.azure.com' was not found`
- Error: `The access token is from the wrong issuer`

**Solution:**
```bash
# List available tenants
az account list --query "[].{name:name, tenantId:tenantId}" -o table

# Login to specific tenant
az login --tenant TENANT_ID

# Verify correct subscription
az account show
```

### "DefaultAzureCredential failed to retrieve a token"

**Problem:** No valid credential found in DefaultAzureCredential chain.

**Solution:** Ensure at least one credential method works:
1. Azure CLI: `az login` (most common)
2. Environment variables: Set `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`
3. Managed Identity: If running on Azure VM/App Service

## RBAC Permission Errors

### "Missing required Azure AI Foundry roles"

**Problem:** User lacks necessary RBAC roles at subscription level.

**Sufficient roles:**
- Azure AI User (minimum)
- Azure AI Owner
- Contributor
- Owner

**Solution (requires admin):**
```bash
az role assignment create \
  --role "Azure AI User" \
  --assignee "user@example.com" \
  --scope /subscriptions/{subscription-id}
```

**Documentation:** https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/rbac-foundry

### "Authorization failed" when creating agents

**Problem:** User has subscription-level role but not resource-level access.

**Solution:** Grant role at resource group or resource level:
```bash
az role assignment create \
  --role "Azure AI User" \
  --assignee "user@example.com" \
  --scope /subscriptions/{sub-id}/resourceGroups/{rg-name}
```

## Quota Issues

### "No Standard or GlobalStandard SKU available"

**Problem:** Model only supports Provisioned deployments (not pay-as-you-go).

**Solution:**
- Choose different model (e.g., use `gpt-4o-mini` instead of large models)
- Request Provisioned quota from Azure support
- Try different region

### "No quota available for any SKU"

**Problem:** All quota exhausted in region.

**Solutions:**
1. **Use existing deployment** - Select existing deployment instead of creating new
2. **Different region** - Create project in region with quota (swedencentral, eastus2 often have availability)
3. **Request quota increase** - Azure Portal → Quotas → Request increase
4. **Delete unused deployments** - Free up quota by removing old deployments

### Checking quota manually

```bash
# View quota usage for a region
az cognitiveservices usage list --location swedencentral -o table

# Look for:
# - Standard or GlobalStandard entries
# - Model name in the quota name
# - Current vs Limit values
```

## Model Availability

### "No models found matching 'model-name'"

**Problem:** Model not available in selected project's region.

**Common model availability:**
- `gpt-4o`: swedencentral, eastus, westus, northcentralus
- `gpt-4o-mini`: Most regions
- `gpt-35-turbo`: Most regions
- `gpt-4`: Select regions only

**Solution:**
- Check model availability: `az cognitiveservices model list --location {region}`
- Choose different model
- Create project in region with model support

### Region recommendations

**Best regions for model availability:**
1. `swedencentral` - Good for GPT-4o, often has quota
2. `eastus2` - Wide model support
3. `eastus` - Wide model support
4. `westus3` - Good availability

## Deployment Issues

### "Resource 'agent-name' already exists"

**Problem:** Agent name already used in project.

**Solution:** Script prompts for new name automatically. Enter different name or 'q' to cancel.

**Checking existing agents:**
```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
agents = client.agents.list()
for agent in agents:
    print(agent.get('name'))
```

### "Deployment name already exists"

**Problem:** Model deployment name conflict.

**Solution:** 
- Choose different deployment name when prompted
- Use existing deployment (select by letter A-Z)

### "Agent creation succeeded but GET failed"

**Problem:** Agent created but verification failed (SDK caching issue).

**Workaround:** Agent was created successfully. Get agent ID from output and test directly:
```bash
python test-agent.py agent-name endpoint
```

## SDK/Dependencies Issues

### "ImportError: No module named 'azure.ai.projects'"

**Problem:** Dependencies not installed.

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

### "AttributeError: 'AgentDefinition' object has no attribute..."

**Problem:** Wrong SDK version (requires 2.0.0b3+).

**Solution:**
```bash
pip install azure-ai-projects==2.0.0b3 --force-reinstall
```

### "API version not supported"

**Problem:** Using outdated SDK with new API features.

**Solution:** Ensure correct versions:
- `azure-ai-projects==2.0.0b3`
- `openai==2.16.0`
- `azure-identity==1.25.1`

## Project/Resource Issues

### "No projects found"

**Problem:** No Azure AI Foundry projects exist.

**Solution:** Create infrastructure:
```bash
./setup-azure-ai.sh myproject swedencentral
```

### "Project management not enabled"

**Problem:** AI Services resource created without `allowProjectManagement=true`.

**Solution:** Enable via REST API (run in setup script) or recreate resource with proper settings.

### "Endpoint not found"

**Problem:** Invalid endpoint format or project doesn't exist.

**Correct format:**
```
https://resource-name.services.ai.azure.com/api/projects/project-name
```

**Not:**
```
https://resource-name.cognitiveservices.azure.com  # Wrong - this is the old format
```

## Testing Issues

### "Agent not found" during testing

**Problem:** Agent name mismatch or wrong endpoint.

**Solution:**
- Verify agent name exactly matches (case-sensitive)
- Check endpoint includes `/api/projects/project-name`
- List agents to confirm name:
  ```bash
  az rest --method GET \
    --url "https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{resource}/projects?api-version=2025-06-01"
  ```

### "Response API error: 'responses' module not found"

**Problem:** Using wrong client method.

**Solution:** Use OpenAI client's responses API:
```python
# Correct
openai_client = client.get_openai_client()
response = openai_client.responses.create(...)

# Wrong
response = client.responses.create(...)  # No responses on AIProjectClient
```

## Getting Help

If issues persist:

1. **Check agent exists:** List agents in project via Azure Portal
2. **Verify RBAC:** Check role assignments in Azure Portal → IAM
3. **Review quotas:** Azure Portal → Quotas & Usage
4. **SDK logs:** Set `AZURE_LOG_LEVEL=DEBUG` for detailed SDK logging
5. **Azure support:** Create support ticket for quota/resource issues

## Useful Commands

```bash
# Check Azure CLI version
az --version

# Check login status
az account show

# List all resources
az resource list --resource-type "Microsoft.CognitiveServices/accounts" -o table

# List deployments
az cognitiveservices account deployment list -n resource-name -g resource-group -o table

# Check role assignments
az role assignment list --assignee user@example.com --subscription {sub-id} -o table
```
