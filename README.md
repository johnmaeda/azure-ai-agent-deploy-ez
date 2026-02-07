# Azure AI Agent Builder Toolkit

Create and deploy prompt-based Azure AI agents using YAML definitions and the Azure AI Projects SDK.

## Installation

### Option 1: Install via npx (Recommended)

If you're using this toolkit as a skill for AI coding agents:

```bash
# Install the skill from GitHub
npx skills add https://github.com/johnmaeda/azure-ai-agent-deploy-ez --skill azure-ai-agent-deploy

# Install Python dependencies
pip install -r .agents/skills/azure-ai-agent-deploy/scripts/requirements.txt

# Login to Azure
az login

# Ready to deploy agents with copilot cli
copilot

# > using the azure agent deploy ez skill create a julia child agent that dispenses recipes with her usual flair

# or even better ....

# > using the azure ai agent deploy ez skill i want to make an agent that emulates james bond style persona using the model gpt-5.2-chat in a resource with the name 'maeda' in it that is regioned in swedencentral if you have to pick a resource

# Or use the scripts directly to deploy a pirate
python .agents/skills/azure-ai-agent-deploy/scripts/create-agent.py .agents/skills/azure-ai-agent-deploy/scripts/agents/examples/pirate-captain.yaml
```



### Option 2: Clone Repository

For direct use or development:

```bash
# Clone repository
git clone https://github.com/johnmaeda/azure-ai-agent-deploy-ez.git
cd azure-ai-agent-deploy-ez

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Login to Azure
az login

# Ready to deploy agents!
python create-agent.py agents/examples/pirate-captain.yaml
```

## Overview

This toolkit provides:
- **YAML-based agent definitions** - Simple frontmatter format for defining agents
- **Automated deployment** - Handles Azure authentication, project selection, model deployment
- **Interactive testing** - CLI tools for testing deployed agents
- **Python API** - Programmatic agent creation and management

## Prerequisites

### Required Software

1. **Python 3.10+**
2. **Azure CLI** - For authentication and resource management
3. **Azure Subscription** - With Azure AI Foundry access

### Azure Requirements

- Azure subscription with appropriate permissions
- **Azure AI User** role (minimum) or Contributor/Owner
- Azure AI Foundry project with deployed models (or use `setup-azure-ai.sh` to create)

## Quick Start

### 1. Install Dependencies

```bash
# Clone repository
git clone https://github.com/johnmaeda/azure-ai-agent-deploy-az.git
cd azure-ai-agent-deploy-az

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Login to Azure

```bash
# Login with browser
az login

# Or use device code (for remote/SSH)
az login --use-device-code

# Verify login
az account show
```

### 3. Create Your First Agent

```bash
# Create agent from YAML (script handles all Azure complexity)
python create-agent.py agents/examples/helpful-assistant.yaml --filter myproject

# Or create a pirate agent!
python create-agent.py agents/examples/pirate-captain.yaml --filter myproject
```

The script will:
1. ✅ Check Azure CLI and login
2. ✅ Verify RBAC permissions
3. ✅ Select Azure AI project
4. ✅ Deploy model (if needed)
5. ✅ Create agent
6. ✅ Save connection info

### 4. Test Your Agent

```bash
# Interactive testing
python test-agent.py agents/examples/helpful-assistant.agent.txt

# Type messages, get responses in real-time
# Type 'exit' or 'quit' to end session
```

## Project Structure

```
azure-ai-agent-deploy-ez/
├── create-agent.py              # Main deployment CLI
├── test-agent.py                # Interactive testing CLI
├── deploy-azure-model.sh        # Model deployment helper
├── setup-azure-ai.sh            # Infrastructure setup
├── requirements.txt             # Python dependencies
├── agents/                      # Core Python module
│   ├── __init__.py
│   ├── yaml_parser.py           # Parse YAML definitions
│   ├── agent_builder.py         # Create agents via SDK
│   └── azure_discovery.py       # Discover Azure resources
├── agents/examples/             # Sample agent definitions
│   ├── helpful-assistant.yaml
│   ├── code-reviewer.yaml
│   ├── pirate-captain.yaml
│   └── math-tutor.yaml
└── etc/                         # Additional examples & docs
    ├── README.md                # Detailed API documentation
    └── *.py                     # Example scripts
```

## Creating Agents

### YAML Format

Define agents using YAML frontmatter:

```yaml
---
name: my-assistant
description: A helpful assistant
model: gpt-4o-mini  # Optional - triggers auto-deployment if not found
---

You are a helpful, friendly assistant. You:
- Answer questions clearly and accurately
- Admit when you don't know something
- Keep responses concise unless asked for detail
```

**Required fields:**
- `name` - Agent identifier (lowercase, hyphens allowed)
- `description` - What the agent does (one sentence)

**Optional fields:**
- `model` - Model hint (e.g., `gpt-4o`, `gpt-4o-mini`) - triggers auto-deployment

### Deployment Commands

```bash
# Basic deployment
python create-agent.py agents/examples/code-reviewer.yaml

# Filter projects (useful for large subscriptions)
python create-agent.py agents/examples/math-tutor.yaml --filter maeda

# Deploy and test immediately
python create-agent.py agents/examples/helpful-assistant.yaml --test
```

### Available Examples

- `helpful-assistant.yaml` - General-purpose assistant
- `code-reviewer.yaml` - Code review specialist
- `data-analyst.yaml` - Data analysis expert
- `math-tutor.yaml` - Math tutoring assistant
- `pirate-captain.yaml` - Pirate-speaking assistant (fun example!)

## Python API

### Using the Agent Builder

```python
from agents.yaml_parser import parse_agent_yaml
from agents.agent_builder import AgentBuilder

# Parse YAML definition
config = parse_agent_yaml('agents/examples/helpful-assistant.yaml')

# Create agent
endpoint = "https://resource.services.ai.azure.com/api/projects/project"
builder = AgentBuilder(endpoint)

agent = builder.create_agent(
    model="gpt-4o-mini",
    name=config.name,
    instructions=config.instructions,
    description=config.description,
)

print(f"Agent created: {agent.agent_id}")

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
    endpoint="https://resource.services.ai.azure.com/api/projects/project",
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

## CLI Tools

### Agent Management

- `create-agent.py` - Deploy agents from YAML
- `test-agent.py` - Interactive agent testing

### Infrastructure Setup

- `setup-azure-ai.sh` - Create Azure AI Foundry infrastructure from scratch
- `deploy-azure-model.sh` - Deploy models to Azure AI resources

### Helper Tools (in etc/)

- `search-azure-ai.sh` - Search for Azure AI resources and projects
- `list-azure-models.sh` - List deployed models
- `test-azure-model.sh` - Test model deployments
- `get-azure-key.sh` - Get API keys and endpoints
- `check-azure-roles.sh` - Verify RBAC permissions

## Setup from Scratch

If you need to create Azure infrastructure:

```bash
# Create resource group, AI Services resource, and project
./setup-azure-ai.sh myproject swedencentral

# Deploy a model
./deploy-azure-model.sh myproject-resource gpt-4o-mini

# Now you can create agents!
python create-agent.py agents/examples/helpful-assistant.yaml --filter myproject
```

## Required Dependencies

### Python Packages (requirements.txt)

```
azure-ai-agents==1.1.0
azure-ai-projects==2.0.0b3    # BETA SDK - required version
azure-core==1.38.0
azure-identity==1.25.1
openai==2.16.0
PyYAML==6.0.3
pydantic==2.12.5
```

**Important:** This project uses `azure-ai-projects==2.0.0b3` (beta) for the new `AgentDefinition` API.

### Azure CLI Installation

```bash
# macOS
brew install azure-cli

# Windows
winget install Microsoft.AzureCLI

# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

## RBAC Permissions

Azure AI Foundry requires specific role-based access control (RBAC) permissions.

**Required roles** (minimum one at subscription level):
- `Azure AI User` - Minimum for building with AI Foundry
- `Azure AI Project Manager` - Create projects and assign roles
- `Contributor` or `Owner` - Full access

**Check your roles:**
```bash
./etc/check-azure-roles.sh
```

**If you lack permissions**, share this with your Azure administrator:
```bash
az role assignment create \
  --role "Azure AI User" \
  --assignee "user@example.com" \
  --scope /subscriptions/{subscription-id}
```

## Troubleshooting

### Common Issues

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'agents'` | Run from project root directory |
| `Agent 'name' already exists` | Script prompts for different name |
| `cannot import name 'AgentDefinition'` | Install exact version: `pip install azure-ai-projects==2.0.0b3` |
| `Token tenant does not match resource tenant` | Run `az login` with correct tenant |
| `No quota available` | Choose different region or model, or request quota increase |
| Not logged into Azure CLI | Run `az login` |
| Missing RBAC permissions | Run `./etc/check-azure-roles.sh` for instructions |

### Setup Verification

Run this to verify your setup:

```bash
# Check all files present
python3 << 'EOF'
from pathlib import Path
required = ["create-agent.py", "test-agent.py", "agents/yaml_parser.py", 
            "agents/agent_builder.py", "agents/azure_discovery.py"]
missing = [f for f in required if not Path(f).exists()]
if missing:
    print(f"❌ Missing: {', '.join(missing)}")
else:
    print("✅ All required files present")
EOF

# Check Python dependencies
python -c "import azure.ai.projects; print(f'✅ azure-ai-projects {azure.ai.projects.__version__}')"

# Check Azure CLI
az --version | head -1
az account show --query name -o tsv
```

## Documentation

- **etc/README.md** - Detailed API documentation and additional examples
- **AGENTS.md** - Developer guide for AI coding agents
- **.agents/skills/azure-ai-agent-deploy/** - Complete skill for agentic deployment

### Azure Resources

- [Azure AI Foundry SDK Overview](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/sdk-overview)
- [Foundry Agent Service Quickstart](https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart)
- [RBAC for Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/rbac-foundry)

## Examples

### Example 1: Helpful Assistant

```yaml
---
name: helpful-assistant
description: A general-purpose helpful assistant
model: gpt-4o-mini
---

You are a helpful, friendly assistant. You:
- Answer questions clearly and accurately
- Admit when you don't know something
- Provide step-by-step guidance when needed
```

### Example 2: Pirate Captain

```yaml
---
name: pirate-captain
description: A friendly pirate captain who speaks in pirate dialect
model: gpt-4o-mini
---

Ahoy! Ye be Captain Blackbeard's AI assistant!

When interactin' with landlubbers:
- Always address folks as "matey," "landlubber," or "me hearty"
- Use pirate expressions like "ahoy," "arrr," and "shiver me timbers"
- Replace "my" with "me," "you" with "ye"
- End responses with "Arrr!" or "Fair winds to ye!"

Despite yer colorful speech, always provide helpful, accurate answers!
```

### Example 3: Code Reviewer

```yaml
---
name: code-reviewer
description: Reviews code for quality and best practices
model: gpt-4o
---

You are an expert code reviewer. When analyzing code, provide:

1. Quality Assessment - Rate code quality (1-10)
2. Security Issues - Identify vulnerabilities
3. Best Practices - Note convention deviations
4. Performance - Highlight inefficiencies
5. Maintainability - Comment on readability

Be constructive and provide code examples for improvements.
```

## Contributing

See **AGENTS.md** for developer guidelines including:
- Code style conventions
- Import organization
- Type hints requirements
- Error handling patterns
- Testing procedures

## License

MIT License - See LICENSE file for details.

---

**Quick Reference:**
- Create agent: `python create-agent.py agents/examples/my-agent.yaml`
- Test agent: `python test-agent.py agents/examples/my-agent.agent.txt`
- Setup Azure: `./setup-azure-ai.sh myproject swedencentral`
- Deploy model: `./deploy-azure-model.sh myresource gpt-4o-mini`
