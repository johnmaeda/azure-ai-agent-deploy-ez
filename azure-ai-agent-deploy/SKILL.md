---
name: azure-ai-agent-deploy
description: Deploy prompt-based Azure AI agents from YAML definitions to Azure AI Foundry projects. Use when users want to (1) create and deploy Azure AI agents, (2) set up Azure AI infrastructure, (3) deploy AI models to Azure, or (4) test deployed agents interactively. Handles authentication, RBAC, quotas, and deployment complexities automatically.
---

# Azure AI Agent Deploy

## Overview

This skill guides the deployment of simple prompt-based Azure AI agents to Azure AI Foundry using YAML definitions. It automates the complex process of Azure authentication, project selection, model deployment, and agent creation while providing clear guidance for users unfamiliar with Azure constraints.

**📦 Self-Contained:** This skill includes all required Python scripts, bash scripts, and the agents module in the `scripts/` directory. No external repository dependencies are needed.

## Quick Start

**Setup:** Copy the `scripts/` directory from this skill to your working directory.

The complete workflow involves 3 steps:

1. **Create agent YAML** - Define agent with name, description, and instructions
2. **Deploy** - Run `create-agent.py` to deploy to Azure (handles all Azure complexity)
3. **Test** - Run `test-agent.py` for interactive testing

**Typical user flow:**
```bash
# Setup (one time)
cp -r scripts/* ./

# Install dependencies
pip install -r requirements.txt
az login

# 1. Create or use example: agents/examples/my-agent.yaml
python create-agent.py agents/examples/helpful-assistant.yaml --filter myproject

# 2. Script handles: Azure auth, project selection, model deployment, agent creation
# Creates: agents/examples/helpful-assistant.agent.txt with connection details

# 3. Test interactively
python test-agent.py agents/examples/helpful-assistant.agent.txt
```

## Agent YAML Format

Agents use YAML frontmatter + instructions format:

```yaml
---
name: agent-name
description: Brief description of what the agent does
model: gpt-4o-mini  # Optional hint - if not found, will prompt/deploy
---

System instructions for the agent go here.
These become the agent's system prompt.

Example instructions:
You are a helpful assistant that specializes in...
```

**Required fields:**
- `name` - Agent identifier (lowercase, hyphens allowed)
- `description` - What the agent does (one sentence)

**Optional fields:**
- `model` - Model hint (e.g., `gpt-4o`, `gpt-4o-mini`) - triggers auto-deployment if not found

Use the template in `assets/template-agent.yaml` for new agents. See `references/yaml-examples.md` for complete examples.

## Deployment Workflow

### Prerequisites Check

The `create-agent.py` script automatically checks:

1. **Azure CLI installed** - Provides install commands if missing
2. **Azure login** - Prompts for device code login if needed
3. **RBAC roles** - Verifies user has Azure AI User/Contributor/Owner role

**If role check fails**, script provides admin command to fix:
```bash
az role assignment create --role "Azure AI User" --assignee "user@example.com" --scope /subscriptions/{sub-id}
```

### Interactive Deployment Steps

The script guides through each step:

**1. Project Selection**
- Lists Azure AI Foundry projects (with optional `--filter` for large subscriptions)
- Auto-selects if only one match
- Shows: `resource-name/project-name location`

**2. Model Deployment Selection**
- Lists current deployments in selected project
- If model hint provided in YAML:
  - Checks for exact match on deployment/model name
  - Checks quota availability in project region
  - Offers to deploy model automatically if not found
- If no model hint: shows all deployments for manual selection
- Can select existing deployment (letter A-Z) or deploy new model (number)

**3. Model Deployment (if needed)**
- Launches `deploy-azure-model.sh` interactively
- Handles:
  - Model availability in region
  - Quota checking (GlobalStandard/Standard SKUs)
  - Capacity configuration (default 10K TPM)
  - Deployment name conflicts

**4. Agent Creation**
- Creates prompt-based agent with AgentKind.PROMPT
- Handles name conflicts - prompts for new name if exists
- Verifies creation with follow-up GET request

**5. Output**
- Saves `.agent.txt` file with connection details and sample code
- Prints test command: `python test-agent.py <agent-name> <endpoint>`

### Command Reference

```bash
# Basic deployment
python create-agent.py agents/examples/code-reviewer.yaml

# Filter projects (useful for large subscriptions)
python create-agent.py agents/examples/math-tutor.yaml --filter maeda

# Deploy and test immediately
python create-agent.py agents/examples/helpful-assistant.yaml --test
```

## Testing Agents

### Interactive Testing

```bash
# Using .agent.txt file (recommended)
python test-agent.py agents/examples/my-agent.agent.txt

# Direct specification
python test-agent.py agent-name https://resource.services.ai.azure.com/api/projects/project-name
```

**Test session features:**
- Interactive chat loop
- Type 'exit' or 'quit' to end
- Ctrl+C to interrupt
- Prints Python code sample after conversation

### Programmatic Usage

The `.agent.txt` file includes sample code:

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

client = AIProjectClient(
    endpoint="https://resource.services.ai.azure.com/api/projects/project",
    credential=DefaultAzureCredential(),
)

openai_client = client.get_openai_client()

response = openai_client.responses.create(
    input=[{"role": "user", "content": "Your message"}],
    extra_body={"agent": {"name": "agent-name", "type": "agent_reference"}},
)

print(response.output_text)
```

## Setup Azure Infrastructure (Optional)

If user needs to create Azure AI Foundry infrastructure from scratch:

```bash
./setup-azure-ai.sh myproject swedencentral
```

Creates:
- Resource group: `rg-myproject`
- AI Services resource: `myproject-resource` (with project management enabled)
- AI Foundry project: `myproject-project`

Returns endpoint and API key for use.

## Model Deployment (Standalone)

To deploy models without creating agents:

```bash
# Interactive deployment
./deploy-azure-model.sh

# With filters
./deploy-azure-model.sh myresource gpt-4o
```

Features:
- Lists available models by region
- Checks quota (GlobalStandard/Standard)
- Configurable capacity (TPM)
- Can select existing deployments

## Important Constraints

### Agent Type
**This skill only covers simple prompt-based agents** (AgentKind.PROMPT). No tools like Code Interpreter, File Search, or custom functions. For tool-enabled agents, see `.agents/skills/hosted-agents-v2-py/`.

### Model Requirements
- Only OpenAI models (gpt-4o, gpt-4o-mini, gpt-4, gpt-35-turbo, etc.)
- Standard or GlobalStandard SKU (not Provisioned)
- Model must be available in project region
- Quota must be available (checked automatically)

### Azure Requirements
- Azure CLI must be installed
- User must be logged in via `az login`
- User needs Azure AI User role minimum (or Contributor/Owner)
- Uses `DefaultAzureCredential()` (never API keys)

### Beta SDK Notice
Uses `azure-ai-projects==2.0.0b3` (beta) - APIs may change. The `AgentDefinition` API is specific to SDK 2.0.0b3+.

## Common Issues

See `references/troubleshooting.md` for detailed solutions to:
- Authentication failures (tenant mismatches)
- RBAC permission errors
- Quota exhaustion
- Model availability by region
- Name conflicts
- SDK version issues

## Bundled Scripts

This skill includes all required scripts and dependencies:

### Main Scripts
- **scripts/create-agent.py** - Main deployment CLI (610 lines)
- **scripts/test-agent.py** - Interactive testing tool (179 lines)
- **scripts/deploy-azure-model.sh** - Model deployment (336 lines)
- **scripts/setup-azure-ai.sh** - Infrastructure setup (140 lines)

### Python Module
- **scripts/agents/** - Core Python module with:
  - `__init__.py` - Module initialization
  - `yaml_parser.py` - YAML frontmatter parser
  - `agent_builder.py` - Agent creation via SDK
  - `azure_discovery.py` - Resource discovery

### Example Agents
- **scripts/agents/examples/** - Agent YAML templates:
  - `helpful-assistant.yaml` - General purpose
  - `code-reviewer.yaml` - Code review
  - `math-tutor.yaml` - Tutoring
  - `data-analyst.yaml` - Data analysis
  - `pirate-captain.yaml` - Fun pirate example

### Configuration
- **scripts/requirements.txt** - Python dependencies

**Usage:** Copy the `scripts/` directory to your working directory to deploy agents.

## Resources

### Setup Documentation
- **README.md** - Complete setup guide with installation and configuration steps

### References
- **troubleshooting.md** - Solutions to common Azure/deployment errors
- **yaml-examples.md** - Complete agent YAML examples for various use cases

### Assets
- **template-agent.yaml** - Clean template for creating new agents
