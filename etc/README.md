# Azure AI Foundry Agent & CLI Tools

Create and manage Azure AI Foundry agents using YAML definitions and the Azure AI Projects SDK.

## Prerequisites

1. **Azure subscription** with access to Azure AI Foundry
2. **Azure CLI** installed and authenticated (`az login`)
3. **Python 3.10+**

## Quick Start

```bash
# 1. Install dependencies (requires SDK 2.0.0b3+)
pip install -r requirements.txt

# 2. Login to Azure and select subscription
./az-login.sh foundry

# 3. Create an agent from YAML
python create-agent.py agents/examples/helpful-assistant.yaml --filter maeda

# 4. Or create a fun pirate agent
export AZURE_AI_PROJECT_ENDPOINT="https://<resource>.services.ai.azure.com/api/projects/<project>"
python fake-pirate-simple.py create
python fake-pirate-simple.py test fake-pirate
```

---

## Creating Agents from YAML

### YAML Format

Define agents using simple YAML frontmatter:

```yaml
---
name: my-assistant
description: A helpful assistant
model: gpt-4o-mini
---

You are a helpful, friendly assistant. You:
- Answer questions clearly and accurately
- Admit when you don't know something
- Keep responses concise unless asked for detail
```

### Create Agent

```bash
python create-agent.py agents/examples/helpful-assistant.yaml --filter maeda
```

The script will:
1. Parse the YAML definition
2. Authenticate with Azure
3. Let you select a project and model deployment
4. Create the agent using the prompt-based API
5. Save usage instructions to a `.agent.txt` file

### Available Examples

- `agents/examples/helpful-assistant.yaml` - General-purpose assistant
- `agents/examples/code-reviewer.yaml` - Code review specialist
- `agents/examples/data-analyst.yaml` - Data analysis expert
- `agents/examples/math-tutor.yaml` - Math tutoring assistant

---

## Pirate Agent Example

A fun example showing prompt-based agent creation:

```bash
# Set your project endpoint
export AZURE_AI_PROJECT_ENDPOINT="https://<resource>.services.ai.azure.com/api/projects/<project>"

# Create the pirate agent
python fake-pirate-simple.py create

# List pirate agents
python fake-pirate-simple.py list

# Chat with the pirate
python fake-pirate-simple.py test fake-pirate

# Delete when done
python fake-pirate-simple.py delete <agent-id>
```

---

## Python API

### Using the Agent Builder

```python
from agents import parse_agent_yaml, AgentBuilder

# Parse YAML definition
config = parse_agent_yaml('agents/examples/helpful-assistant.yaml')

# Create agent
builder = AgentBuilder(endpoint="https://<resource>.services.ai.azure.com/api/projects/<project>")
agent = builder.create_agent(
    model="gpt-4o-mini",
    name=config.name,
    instructions=config.instructions,
)

print(agent)  # Shows agent ID, name, model, endpoint

# Test the agent
response = builder.test_agent(agent.name, "Hello!")
print(response)

# List all agents
agents = builder.list_agents()

# Delete an agent
builder.delete_agent(agent.agent_id)
```

### Using the Responses API Directly

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

client = AIProjectClient(
    endpoint="https://<resource>.services.ai.azure.com/api/projects/<project>",
    credential=DefaultAzureCredential(),
)

# Get OpenAI client for responses API
openai_client = client.get_openai_client()

# Chat with an agent by name
response = openai_client.responses.create(
    input=[{"role": "user", "content": "Hello!"}],
    extra_body={"agent": {"name": "my-assistant", "type": "agent_reference"}},
)

print(response.output_text)
```

---

## CLI Tools

### az-login.sh

Login to Azure and select a subscription with filtering.

```bash
./az-login.sh [filter]
./az-login.sh                # Show all subscriptions
./az-login.sh foundry        # Filter by 'foundry'
```

### search-azure-ai.sh

Search for Azure AI resources and projects.

```bash
./search-azure-ai.sh [filter]
./search-azure-ai.sh maeda        # Filter by 'maeda'
```

### list-azure-models.sh

List deployed models in an Azure AI resource.

```bash
./list-azure-models.sh [filter]
./list-azure-models.sh maeda
```

### deploy-azure-model.sh

Deploy a model to an Azure AI resource.

```bash
./deploy-azure-model.sh [resource-filter] [model-filter]
./deploy-azure-model.sh maeda gpt-4o-mini
```

### test-azure-model.sh

Test a deployed model with a chat completion request.

```bash
./test-azure-model.sh [resource-filter] [deployment-name]
./test-azure-model.sh maeda gpt-4o-mini
```

### get-azure-key.sh

Get the API key and endpoint for an Azure AI resource.

```bash
./get-azure-key.sh [filter]
./get-azure-key.sh maeda
```

### check-azure-roles.sh

Check if you have the required Azure RBAC roles to use Azure AI Foundry.

```bash
./check-azure-roles.sh
```

**Why this matters:** Azure AI Foundry requires specific role-based access control (RBAC) permissions. Without the proper roles (like `Azure AI User`), API calls will fail even if you can log in to Azure.

The script checks your **subscription-level** role assignments and tells you:
- Whether you have sufficient access (Azure AI User, Contributor, Owner, etc.)
- If not, provides the exact `az` command and information to share with your administrator

**Required roles** (at minimum one):
- `Azure AI User` - Minimum for building with AI Foundry
- `Azure AI Project Manager` - Create projects and assign AI User role
- `Contributor` or `Owner` - Full access (inherits down to all resources)

**Reference docs:**
- [RBAC for Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/rbac-foundry)
- [Check Access in Azure](https://learn.microsoft.com/en-us/azure/role-based-access-control/check-access)

---

## SDK Requirements

This project uses the **Azure AI Projects SDK 2.0.0b3** (beta) for prompt-based agent creation:

```bash
pip install azure-ai-projects==2.0.0b3 azure-identity
```

Key imports for the new API:

```python
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AgentDefinition, AgentKind
from azure.core.exceptions import ResourceExistsError
```

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| `Agent 'name' already exists` | You'll be prompted to enter a different name |
| `cannot import name 'AgentDefinition'` | Upgrade SDK: `pip install azure-ai-projects==2.0.0b3 --pre` |
| `'AzureKeyCredential' has no attribute 'get_token'` | Use `DefaultAzureCredential()`, not API key |
| `Token tenant does not match resource tenant` | Run `az login` and select correct subscription |
| Model not found | Deploy the model first: `./deploy-azure-model.sh` |

---

## Documentation

- [Azure AI Foundry SDK Overview](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/sdk-overview)
- [Foundry Agent Service Quickstart](https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart)
