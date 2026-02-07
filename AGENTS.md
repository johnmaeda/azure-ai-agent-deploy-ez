# AGENTS.md - Developer Guide for AI Coding Agents

This guide provides coding agents with essential information about working in this repository.

## Project Overview

This is a Python-based Azure AI agent builder toolkit that creates and deploys prompt-based agents to Azure AI Foundry projects. The project uses YAML frontmatter for agent definitions and provides interactive CLI tools for deployment and testing.

**Key Technologies**: Python 3.10+, Azure AI Projects SDK (beta), Azure CLI, PyYAML, OpenAI SDK

## Build, Lint, and Test Commands

### Environment Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Azure CLI login (required for all operations)
az login
```

### Running the Main Tools
```bash
# Create an agent from YAML
python create-agent.py agents/examples/code-reviewer.yaml

# Create with project filtering
python create-agent.py agents/examples/math-tutor.yaml --filter maeda

# Test an agent interactively
python test-agent.py math-tutor https://project.services.ai.azure.com/api/projects/my-project
python test-agent.py agents/examples/math-tutor.agent.txt

# Deploy a model to Azure
./deploy-azure-model.sh

# Set up Azure infrastructure
./setup-azure-ai.sh
```

### Testing Individual Modules
This project uses **manual testing** with `if __name__ == "__main__":` blocks. No pytest or unittest framework exists.

```bash
# Test YAML parser
python -m agents.yaml_parser

# Test agent builder (requires AZURE_AI_PROJECT_ENDPOINT env var)
export AZURE_AI_PROJECT_ENDPOINT="https://resource.services.ai.azure.com/api/projects/project-name"
python -m agents.agent_builder

# Test Azure discovery
python -m agents.azure_discovery
```

### Linting and Formatting
**No linters configured** - follow the style patterns documented below.

## Code Style Guidelines

### Import Organization
Order: Standard library → Third-party → Local imports. Always use explicit imports.

```python
# Standard library
import json
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Third-party
import yaml
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AgentDefinition, AgentKind

# Local
from agents.yaml_parser import parse_agent_yaml, AgentConfig
```

**Always use** `from module import specific_names` (not `import module`)

### Type Hints
Use type hints for **all function signatures**. Use modern Python 3.10+ syntax.

```python
# CORRECT: Modern union syntax and built-in generics
def parse_agent_yaml(file_path: str | Path) -> AgentConfig:
    """Parse an agent YAML file."""

def list_resources(self, filter_term: str = "") -> list[AzureResource]:
    """List Azure AI resources."""

# INCORRECT: Old typing module syntax
def parse_agent_yaml(file_path: Union[str, Path]) -> AgentConfig:  # Don't use Union
def list_resources(self, filter_term: str = "") -> List[AzureResource]:  # Don't use List
```

**Use dataclasses** for structured data:
```python
@dataclass
class AgentConfig:
    name: str
    description: str
    instructions: str
    model_hint: Optional[str] = None
```

### Naming Conventions
- **Variables/Functions**: `snake_case` - `deployment_name`, `create_agent()`, `list_deployments()`
- **Classes**: `PascalCase` - `AgentBuilder`, `AzureDiscovery`, `CreatedAgent`
- **Constants**: `UPPER_CASE` - `SUFFICIENT_ROLES`, `DEFAULT_MODEL`
- **Private methods**: Prefix with `_` - `_get_client()`, `_run_az()`, `_check_cli()`
- **Boolean returns**: Start with verb - `is_logged_in()`, `check_azure_cli()`

### Error Handling
Provide **helpful error messages** with actionable solutions. Handle expected errors gracefully.

```python
# Pattern 1: Try-except with helpful messages
try:
    config = parse_agent_yaml(yaml_path)
except Exception as e:
    print(f"\nError parsing YAML: {e}")
    sys.exit(1)

# Pattern 2: Check and guide user
result = subprocess.run(["az", "--version"], capture_output=True, text=True)
if result.returncode != 0:
    print("\n❌ Azure CLI is not installed.")
    print("\n   Install instructions:")
    print("   macOS:   brew install azure-cli")
    return False

# Pattern 3: Resource conflicts with retry
while True:
    try:
        agent = client.agents.create(name=current_name, definition=definition)
        break
    except ResourceExistsError:
        print(f"\n⚠️  Agent '{current_name}' already exists.")
        new_name = input("Enter a different name (or 'q' to cancel): ").strip()
        if new_name.lower() == 'q':
            raise RuntimeError(f"Agent creation cancelled")
        current_name = new_name

# Pattern 4: Graceful degradation
try:
    agents = client.agents.list()
    return [{"id": a.get('id'), "name": a.get('name')} for a in agents]
except Exception as e:
    print(f"Warning: Could not list agents: {e}")
    return []
```

### Documentation
All modules and functions must have docstrings. Use Google-style for complex functions.

```python
def create_agent(
    self,
    model: str,
    name: str,
    instructions: str,
    description: str = "",
) -> CreatedAgent:
    """
    Create an Azure AI prompt-based agent using the SDK.
    
    Args:
        model: Model deployment name (e.g., "gpt-4o-mini")
        name: Agent name
        instructions: System instructions for the agent
        description: Optional description
        
    Returns:
        CreatedAgent with agent details
    """
```

Use inline comments to explain **why**, not what:
```python
# Force fresh client to avoid any SDK caching issues
self._client = None
client = self._get_client()
```

### User Experience Patterns
This project prioritizes **interactive CLI UX**. Follow these patterns:

```python
# Section headers
print(f"\n{'=' * 60}")
print(f" Creating Azure AI Agent")
print('=' * 60)

# Status indicators with emojis
print("✅ Azure CLI is installed")
print("❌ Missing required roles")
print("🚀 Launching model deployment...")
print("📦 Creating agent...")

# Progress feedback
print(f"\nFetching deployments in {project.resource_name}...")
print("(Awaiting response...)")

# User confirmations
response = input("Create agent? (Y/n): ").strip().lower()
if response == 'n':
    print("Cancelled.")
    sys.exit(0)
```

### Azure SDK Patterns
This project uses **beta SDK** `azure-ai-projects==2.0.0b3` with specific patterns.

```python
# Always use DefaultAzureCredential (never API keys in code)
from azure.identity import DefaultAzureCredential
credential = DefaultAzureCredential()

# Create client with endpoint
client = AIProjectClient(endpoint=endpoint, credential=credential)

# Use new AgentDefinition API (SDK 2.0.0b3+)
from azure.ai.projects.models import AgentDefinition, AgentKind

definition = AgentDefinition()
definition['kind'] = AgentKind.PROMPT
definition['instructions'] = instructions
definition['model'] = model

agent = client.agents.create(name=name, definition=definition)

# Verify creation immediately
agent = client.agents.get(agent_id)

# Use OpenAI SDK for responses API
from openai import AzureOpenAI
openai_client = AzureOpenAI(
    api_version="2025-01-01-preview",
    azure_endpoint=endpoint,
    azure_ad_token_provider=get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
)
response = openai_client.responses.create(agent_id=agent_id, input=message)
```

## Project Structure

```
test-feb26-build-agent/
├── agents/                      # Core Python module
│   ├── yaml_parser.py           # Parse YAML frontmatter
│   ├── agent_builder.py         # Create agents via SDK
│   ├── azure_discovery.py       # Discover Azure resources
│   └── examples/                # Sample agent YAML files
├── etc/                         # Utilities and examples
│   ├── README.md                # Main documentation
│   ├── *.py                     # Example agents
│   └── *.sh                     # Azure CLI scripts
├── .agents/skills/              # Advanced agent patterns
├── create-agent.py              # Main CLI tool (610 lines)
├── test-agent.py                # Agent testing tool (179 lines)
├── deploy-azure-model.sh        # Model deployment (336 lines)
├── setup-azure-ai.sh            # Infrastructure setup (140 lines)
└── requirements.txt             # Python dependencies
```

## Important Notes for Agents

1. **No formal test suite exists** - use manual testing via `if __name__ == "__main__":` blocks
2. **Beta SDK** - This project uses `azure-ai-projects==2.0.0b3` which may have breaking changes
3. **Authentication** - Always use `DefaultAzureCredential()`, never hardcode API keys
4. **Interactive flows** - User input via `input()` is common; handle `KeyboardInterrupt`
5. **Azure CLI required** - All scripts depend on `az` CLI being installed and logged in
6. **YAML format** - Agent definitions use frontmatter (metadata) + instructions (body)
7. **Emoji indicators** - Use emojis for visual feedback (✅ ❌ 🚀 📦 ⚠️)
8. **Error messages** - Must be actionable with next steps or installation commands
9. **No linter** - Follow patterns in existing code for consistency

## Common Operations

### Adding a New Agent Example
1. Create YAML file in `agents/examples/` with frontmatter format
2. Include `name`, `description`, `model` fields in frontmatter
3. Write system instructions in body after frontmatter separator

### Modifying Agent Creation Logic
Main file: `agents/agent_builder.py` - `AgentBuilder.create_agent()`
- Uses `AgentDefinition` with `AgentKind.PROMPT`
- Handles `ResourceExistsError` with interactive retry
- Verifies agent creation with follow-up GET request

### Adding New Azure Discovery Features
Main file: `agents/azure_discovery.py` - `AzureDiscovery` class
- Uses `subprocess.run()` to call `az` CLI commands
- Parse JSON output with `json.loads()`
- Returns dataclass instances for type safety

### Testing Changes
```bash
# Always test in a virtual environment
source venv/bin/activate

# Test individual modules
python -m agents.yaml_parser
python -m agents.azure_discovery

# Test full workflow
python create-agent.py agents/examples/helpful-assistant.yaml --filter <your-filter>

# Interactive agent testing
python test-agent.py <agent-name> <endpoint>
```

## Files to Read First
1. `etc/README.md` - Comprehensive project documentation
2. `agents/yaml_parser.py` - Understand agent definition format
3. `agents/agent_builder.py` - Core agent creation logic
4. `create-agent.py` - End-to-end workflow example
