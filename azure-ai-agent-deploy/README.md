# Azure AI Agent Deploy Skill - Setup Guide

This guide explains how to set up the environment required for the **azure-ai-agent-deploy** skill to function properly.

## Overview

The **azure-ai-agent-deploy** skill helps deploy prompt-based Azure AI agents from YAML definitions. It depends on several Python scripts and modules that must be present in your repository.

## Required Dependencies

### 1. Python Scripts (Root Directory)

These scripts provide the main deployment and testing functionality:

```
create-agent.py       # Main deployment script (610 lines)
test-agent.py         # Interactive testing tool (179 lines)
deploy-azure-model.sh # Model deployment helper (336 lines)
setup-azure-ai.sh     # Infrastructure setup (140 lines)
```

**Download these files from:**
- Repository: `azure-ai-agent-deploy-ez`
- Direct copy required: All 4 files must be executable

### 2. Python Module (agents/)

The `agents/` module contains core libraries:

```
agents/
├── __init__.py           # Module initialization
├── yaml_parser.py        # Parse YAML frontmatter (137 lines)
├── agent_builder.py      # Create agents via SDK (220 lines)
└── azure_discovery.py    # Discover Azure resources (287 lines)
```

**Download this directory from:**
- Repository: `azure-ai-agent-deploy-ez/agents/`
- All 4 files required for the skill to function

### 3. Python Dependencies (requirements.txt)

```txt
azure-ai-agents==1.1.0
azure-ai-projects==2.0.0b3
azure-core==1.38.0
azure-identity==1.25.1
openai==2.16.0
PyYAML==6.0.3
pydantic==2.12.5
```

**Key dependencies:**
- `azure-ai-projects==2.0.0b3` - **BETA SDK** (required for AgentDefinition API)
- `azure-identity` - Azure authentication
- `openai` - Responses API for agent testing
- `PyYAML` - YAML parsing

### 4. Azure CLI

Required for authentication and resource management:

```bash
# macOS
brew install azure-cli

# Windows
winget install Microsoft.AzureCLI

# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

## Setup Instructions

### Step 1: Create Project Structure

```bash
# Create a new project directory
mkdir my-agent-project
cd my-agent-project

# Create required directories
mkdir -p agents/examples
```

### Step 2: Copy Required Files

**Option A: Clone from repository**
```bash
# Clone the repository
git clone https://github.com/johnmaeda/azure-ai-agent-deploy-ez.git
cd azure-ai-agent-deploy-ez

# Files are already in place
```

**Option B: Manual setup (if starting fresh)**
```bash
# Copy the 4 main scripts to root
# - create-agent.py
# - test-agent.py
# - deploy-azure-model.sh
# - setup-azure-ai.sh

# Copy the agents module
# - agents/__init__.py
# - agents/yaml_parser.py
# - agents/agent_builder.py
# - agents/azure_discovery.py

# Make scripts executable
chmod +x create-agent.py test-agent.py deploy-azure-model.sh setup-azure-ai.sh
```

### Step 3: Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Verify installation:**
```bash
python -c "import azure.ai.projects; print('Azure AI Projects:', azure.ai.projects.__version__)"
python -c "import yaml; print('PyYAML installed')"
```

### Step 4: Install and Configure Azure CLI

```bash
# Install Azure CLI (see above for platform-specific commands)

# Verify installation
az --version

# Login to Azure
az login

# Verify subscription access
az account show
```

### Step 5: Verify Setup

Run this verification script:

```bash
python3 << 'EOF'
import sys
from pathlib import Path

# Check files exist
required_files = [
    "create-agent.py",
    "test-agent.py",
    "deploy-azure-model.sh",
    "setup-azure-ai.sh",
    "agents/__init__.py",
    "agents/yaml_parser.py",
    "agents/agent_builder.py",
    "agents/azure_discovery.py",
    "requirements.txt",
]

print("Checking required files...")
missing = []
for f in required_files:
    if Path(f).exists():
        print(f"  ✅ {f}")
    else:
        print(f"  ❌ {f} - MISSING")
        missing.append(f)

if missing:
    print(f"\n❌ Missing {len(missing)} required file(s)")
    sys.exit(1)
else:
    print("\n✅ All required files present!")

# Check Python imports
print("\nChecking Python dependencies...")
try:
    import azure.ai.projects
    print(f"  ✅ azure-ai-projects {azure.ai.projects.__version__}")
except ImportError:
    print("  ❌ azure-ai-projects - NOT INSTALLED")
    sys.exit(1)

try:
    import yaml
    print("  ✅ PyYAML")
except ImportError:
    print("  ❌ PyYAML - NOT INSTALLED")
    sys.exit(1)

try:
    from azure.identity import DefaultAzureCredential
    print("  ✅ azure-identity")
except ImportError:
    print("  ❌ azure-identity - NOT INSTALLED")
    sys.exit(1)

print("\n✅ Setup complete! Ready to deploy agents.")
EOF
```

## Quick Start After Setup

### Create Your First Agent

1. **Create agent YAML:**

```bash
cat > agents/examples/my-agent.yaml << 'EOF'
---
name: my-agent
description: A helpful assistant
model: gpt-4o-mini
---

You are a helpful assistant. When users ask questions:
- Provide clear, accurate answers
- Be friendly and professional
- Admit when you don't know something
EOF
```

2. **Deploy to Azure:**

```bash
python create-agent.py agents/examples/my-agent.yaml --filter myproject
```

The script will:
- ✅ Check Azure CLI and login
- ✅ Verify RBAC permissions
- ✅ Select Azure AI project
- ✅ Deploy model (if needed)
- ✅ Create agent
- ✅ Save connection info to `my-agent.agent.txt`

3. **Test the agent:**

```bash
python test-agent.py agents/examples/my-agent.agent.txt
```

## Troubleshooting Setup

### "ModuleNotFoundError: No module named 'agents'"

**Problem:** The `agents/` directory is missing or not in the right location.

**Solution:**
```bash
# Ensure agents/ is in the same directory as create-agent.py
ls -la agents/
# Should show: __init__.py, yaml_parser.py, agent_builder.py, azure_discovery.py
```

### "ImportError: cannot import name 'AgentDefinition'"

**Problem:** Wrong version of azure-ai-projects installed.

**Solution:**
```bash
pip install azure-ai-projects==2.0.0b3 --force-reinstall
```

### "FileNotFoundError: create-agent.py not found"

**Problem:** Scripts not in current directory.

**Solution:**
```bash
# Run from the directory containing the scripts
cd /path/to/project/root
ls create-agent.py  # Should exist
```

### "Azure CLI not found"

**Problem:** Azure CLI not installed or not in PATH.

**Solution:**
```bash
# Install Azure CLI (see Step 4 above)
# Verify it's in PATH
which az  # Should show: /usr/local/bin/az or similar
```

## Minimum File Checklist

Before the skill can work, ensure you have:

```
✅ create-agent.py          - Main deployment script
✅ test-agent.py            - Testing tool
✅ deploy-azure-model.sh    - Model deployment
✅ setup-azure-ai.sh        - Infrastructure setup
✅ agents/__init__.py       - Module init
✅ agents/yaml_parser.py    - YAML parsing
✅ agents/agent_builder.py  - Agent creation
✅ agents/azure_discovery.py - Resource discovery
✅ requirements.txt         - Python dependencies
✅ agents/examples/         - Directory for agent YAMLs (can be empty)
```

## Directory Structure

Correct project structure:

```
my-agent-project/
├── create-agent.py              # Main CLI
├── test-agent.py                # Testing CLI
├── deploy-azure-model.sh        # Model deployment
├── setup-azure-ai.sh            # Infrastructure setup
├── requirements.txt             # Python deps
├── venv/                        # Virtual environment
├── agents/                      # Core module
│   ├── __init__.py
│   ├── yaml_parser.py
│   ├── agent_builder.py
│   └── azure_discovery.py
└── agents/examples/             # Agent definitions
    ├── my-agent.yaml
    └── my-agent.agent.txt       # Created after deployment
```

## Getting the Files

### From GitHub Repository

```bash
# Clone the complete repository
git clone https://github.com/johnmaeda/azure-ai-agent-deploy-ez.git
cd azure-ai-agent-deploy-ez

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Login to Azure
az login

# Ready to use!
```

### Manual Download

If you need to download files individually:

1. Visit: `https://github.com/johnmaeda/azure-ai-agent-deploy-ez`
2. Download these files:
   - `create-agent.py`
   - `test-agent.py`
   - `deploy-azure-model.sh`
   - `setup-azure-ai.sh`
   - `requirements.txt`
3. Download entire `agents/` directory
4. Follow setup instructions above

## Azure Prerequisites

### Required Azure Resources

You need either:

**Option A: Existing Azure AI Foundry project**
- Azure subscription with appropriate permissions
- Azure AI User role (minimum) or Contributor/Owner
- Existing AI Foundry project with deployed models

**Option B: Create new infrastructure**
```bash
# Creates everything from scratch
./setup-azure-ai.sh myproject swedencentral
```

### Required Azure Roles

Minimum RBAC role at subscription level:
- **Azure AI User** (minimum)
- **Contributor** (recommended)
- **Owner** (full access)

Admin can assign role:
```bash
az role assignment create \
  --role "Azure AI User" \
  --assignee "user@example.com" \
  --scope /subscriptions/{subscription-id}
```

## Support

### Common Issues

See the skill's `references/troubleshooting.md` for:
- Authentication failures
- RBAC permission errors
- Quota issues
- Model availability
- SDK version problems

### Getting Help

1. Run the verification script (Step 5)
2. Check Azure CLI: `az account show`
3. Verify Python deps: `pip list | grep azure`
4. Review troubleshooting guide in skill

## Version Requirements

**Python:** 3.10 or higher
**Azure CLI:** 2.50.0 or higher (latest recommended)
**SDK:** azure-ai-projects 2.0.0b3 (beta - exact version required)

## Next Steps

Once setup is complete:

1. Review example agents in `agents/examples/`
2. Check skill's `references/yaml-examples.md` for more examples
3. Create your first agent with `create-agent.py`
4. Test with `test-agent.py`

The skill will now work correctly with all dependencies in place!
