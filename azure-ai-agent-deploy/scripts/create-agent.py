#!/usr/bin/env python3
"""
Create Azure AI Agent from YAML Definition

Usage:
    python create-agent.py agents/examples/code-reviewer.yaml
    python create-agent.py my-agent.yaml --filter maeda
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Add agents module to path
sys.path.insert(0, str(Path(__file__).parent))

# Check dependencies before importing
try:
    import yaml
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
except ImportError as e:
    print(f"\n❌ Missing required Python dependencies: {e}")
    print("\n   Install with:")
    print("   pip install azure-ai-projects==2.0.0b3 azure-identity PyYAML openai")
    print("\n   Or if you have requirements.txt:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

from agents.yaml_parser import parse_agent_yaml, AgentConfig
from agents.azure_discovery import AzureDiscovery, AzureProject, ModelDeployment, select_from_list
from agents.agent_builder import AgentBuilder


# Roles that grant sufficient access for Azure AI Foundry
SUFFICIENT_ROLES = {
    "Owner", "Contributor",
    "Azure AI User", "Azure AI Owner", 
    "Azure AI Account Owner", "Azure AI Project Manager"
}


def check_azure_roles() -> bool:
    """
    Check if the current user has sufficient Azure roles for AI Foundry.
    Assumes check_azure_cli() has already verified az CLI and login.
    
    Returns:
        True if roles are sufficient, False otherwise (after printing help).
    """
    print_header("Checking Azure Roles")
    
    # Get account info (already verified logged in by check_azure_cli)
    result = subprocess.run(
        ["az", "account", "show"],
        capture_output=True, text=True
    )
    account = json.loads(result.stdout)
    subscription_id = account.get("id")
    subscription_name = account.get("name")
    
    # Get current user ID
    result = subprocess.run(
        ["az", "ad", "signed-in-user", "show", "--query", "id", "-o", "tsv"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        # Might be a service principal, skip role check
        print("\n⚠️  Could not determine user identity (may be service principal).")
        print("   Proceeding anyway...")
        return True
    
    user_id = result.stdout.strip()
    
    # Get user principal name for display
    result = subprocess.run(
        ["az", "ad", "signed-in-user", "show", "--query", "userPrincipalName", "-o", "tsv"],
        capture_output=True, text=True
    )
    user_name = result.stdout.strip() if result.returncode == 0 else user_id
    
    print(f"\n   User: {user_name}")
    print(f"   Subscription: {subscription_name}")
    
    # Get subscription-level role assignments
    sub_scope = f"/subscriptions/{subscription_id}"
    result = subprocess.run(
        ["az", "role", "assignment", "list", 
         "--assignee", user_id, 
         "--scope", sub_scope,
         "--query", f"[?scope=='{sub_scope}'].roleDefinitionName",
         "-o", "json"],
        capture_output=True, text=True
    )
    
    roles = []
    if result.returncode == 0 and result.stdout.strip():
        try:
            roles = json.loads(result.stdout)
        except json.JSONDecodeError:
            roles = []
    
    # Check for sufficient roles
    found_roles = set(roles) & SUFFICIENT_ROLES
    
    if found_roles:
        print(f"\n   ✅ Roles: {', '.join(found_roles)}")
        return True
    
    # No sufficient roles found
    print("\n❌ Missing required Azure AI Foundry roles.")
    print()
    print("   Share this with your Azure administrator:")
    print("   ─" * 30)
    print(f"   User:  {user_name}")
    print(f"   Role:  Azure AI User (minimum)")
    print(f"   Scope: {sub_scope}")
    print()
    print("   Command for admin to run:")
    print(f'   az role assignment create --role "Azure AI User" --assignee "{user_name}" --scope {sub_scope}')
    print()
    print("   Docs: https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/rbac-foundry")
    return False


def check_azure_cli() -> bool:
    """
    Check if Azure CLI is installed and user is logged in.
    
    Returns:
        True if az CLI is ready, False otherwise (after printing help).
    """
    print_header("Prerequisites Check")
    
    # Check if az CLI is available
    try:
        result = subprocess.run(
            ["az", "--version"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise FileNotFoundError()
        
        # Extract version from first line
        version_line = result.stdout.split('\n')[0] if result.stdout else "azure-cli (version unknown)"
        print(f"\n   ✅ Azure CLI installed: {version_line}")
        
    except FileNotFoundError:
        print("\n❌ Azure CLI is not installed.")
        print()
        print("   The Azure CLI (az) is required to create agents.")
        print()
        print("   Install instructions:")
        print("   ─" * 30)
        print("   macOS:   brew install azure-cli")
        print("   Windows: winget install Microsoft.AzureCLI")
        print("   Linux:   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash")
        print()
        print("   Or visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
        return False
    
    # Check if logged in
    result = subprocess.run(
        ["az", "account", "show"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("\n❌ Not logged into Azure CLI.")
        print()
        print("   Run one of these commands to login:")
        print("   ─" * 30)
        print("   az login                    # Browser-based login")
        print("   az login --use-device-code  # Device code login (for remote/SSH)")
        return False
    
    account = json.loads(result.stdout)
    print(f"   ✅ Logged in to subscription: {account.get('name')}")
    
    return True


def print_header(text: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f" {text}")
    print('=' * 60)


def print_agent_config(config: AgentConfig):
    """Display parsed agent configuration."""
    print()
    print(f"  Name:        {config.name}")
    print(f"  Description: {config.description}")
    if config.model_hint:
        print(f"  Model hint:  {config.model_hint}")
    print(f"  Instructions: {config.instructions[:80]}...")


def select_project(discovery: AzureDiscovery, filter_term: str = "") -> AzureProject:
    """Let user select an Azure AI project."""
    print_header("Select Azure AI Project")
    
    print(f"\nSearching for projects{f' matching \"{filter_term}\"' if filter_term else ''}...")
    projects = discovery.list_projects(filter_term)
    
    if not projects:
        print("No projects found.")
        print("\nTip: Create a project with: ./setup-azure-ai.sh myproject swedencentral")
        sys.exit(1)
    
    def display_project(p: AzureProject) -> str:
        return f"{p.resource_name}/{p.name:<25} {p.location}"
    
    idx = select_from_list(projects, "Select project", display_project)
    
    if idx is None:
        print("No project selected.")
        sys.exit(1)
    
    return projects[idx]


def _check_model_quota(location: str, model_name: str) -> tuple[bool, str]:
    """
    Check if quota is available for a model in a given location.
    
    Args:
        location: Azure region (e.g., 'swedencentral')
        model_name: Model name to check (e.g., 'gpt-4o')
        
    Returns:
        (has_quota, message) - tuple of availability and status message
    """
    try:
        # Get quota usage for the location
        result = subprocess.run(
            ["az", "cognitiveservices", "usage", "list",
             "--location", location,
             "-o", "json"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            return True, "(quota check unavailable)"  # Proceed anyway
        
        usages = json.loads(result.stdout) if result.stdout.strip() else []
        
        # Look for matching quota entries (Standard or GlobalStandard)
        model_lower = model_name.lower()
        for usage in usages:
            name = usage.get("name", {}).get("value", "").lower()
            
            # Skip non-relevant quota types
            if any(x in name for x in ["finetune", "batch", "realtime", "audio", "transcribe", "tts", "diarize"]):
                continue
            
            # Check if this is a matching model with Standard/GlobalStandard
            if model_lower in name and ("standard" in name or "globalstandard" in name):
                current = int(usage.get("currentValue", 0))
                limit = int(usage.get("limit", 0))
                available = limit - current
                
                if available > 0:
                    sku_type = "GlobalStandard" if "globalstandard" in name else "Standard"
                    return True, f"{sku_type}: {available}K TPM available"
        
        return False, "No Standard/GlobalStandard quota available"
        
    except Exception as e:
        return True, f"(quota check error: {e})"  # Proceed anyway on error


def _deploy_model(resource_name: str, model_filter: str) -> bool:
    """
    Run deploy-azure-model.sh to deploy a model.
    
    Args:
        resource_name: Azure AI resource name
        model_filter: Model name filter (e.g., 'gpt-4o')
        
    Returns:
        True if deployment was successful
    """
    script_path = Path(__file__).parent / "deploy-azure-model.sh"
    
    if not script_path.exists():
        print(f"\n❌ Deploy script not found: {script_path}")
        return False
    
    print(f"\n🚀 Launching model deployment...")
    print(f"   Resource: {resource_name}")
    print(f"   Model filter: {model_filter}")
    print()
    
    try:
        # Run the deploy script interactively
        result = subprocess.run(
            [str(script_path), resource_name, model_filter],
            cwd=Path(__file__).parent,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"\n❌ Error running deploy script: {e}")
        return False


def select_deployment(discovery: AzureDiscovery, project: AzureProject, model_hint: str = "") -> ModelDeployment:
    """Let user select a deployed model."""
    print_header("Select Model Deployment")
    
    print(f"\nFetching deployments in {project.resource_name}...")
    deployments = discovery.list_deployments(project.resource_name, project.resource_group)
    
    if not deployments:
        print("No model deployments found.")
        print(f"\nTip: Deploy a model with: ./deploy-azure-model.sh {project.resource_name}")
        if model_hint:
            # Check quota before offering to deploy
            has_quota, quota_msg = _check_model_quota(project.location, model_hint)
            if has_quota:
                print(f"\n   📊 Quota for '{model_hint}' in {project.location}: {quota_msg}")
                response = input(f"\nDeploy '{model_hint}' now? (Y/n): ").strip().lower()
                if response != 'n':
                    if _deploy_model(project.resource_name, model_hint):
                        # Refresh deployments after successful deploy
                        print("\nRefreshing deployments...")
                        deployments = discovery.list_deployments(project.resource_name, project.resource_group)
                        if not deployments:
                            print("Still no deployments found after deploy attempt.")
                            sys.exit(1)
                    else:
                        sys.exit(1)
            else:
                print(f"\n   ❌ Cannot deploy '{model_hint}': {quota_msg}")
                print(f"      Try a different region or request quota increase.")
                sys.exit(1)
        else:
            sys.exit(1)
    
    # If model hint provided, try to find matching deployment
    if model_hint:
        hint_lower = model_hint.lower()
        
        # First pass: exact match on deployment name or model name
        for d in deployments:
            if hint_lower == d.deployment_name.lower() or hint_lower == d.model_name.lower():
                print(f"\nAuto-selecting deployment matching '{model_hint}': {d.deployment_name}")
                return d
        
        # Second pass: substring match (but ask for confirmation)
        partial_matches = []
        for d in deployments:
            if hint_lower in d.deployment_name.lower() or hint_lower in d.model_name.lower():
                partial_matches.append(d)
        
        if len(partial_matches) == 1:
            d = partial_matches[0]
            print(f"\nNo exact match for '{model_hint}', closest: {d.deployment_name}")
            response = input(f"Use '{d.deployment_name}'? (Y/n): ").strip().lower()
            if response != 'n':
                return d
            # User declined partial match - check quota before offering to deploy
            has_quota, quota_msg = _check_model_quota(project.location, model_hint)
            if has_quota:
                print(f"\n   📊 Quota for '{model_hint}' in {project.location}: {quota_msg}")
                response = input(f"Deploy '{model_hint}' instead? (Y/n): ").strip().lower()
                if response != 'n':
                    if _deploy_model(project.resource_name, model_hint):
                        print("\nRefreshing deployments...")
                        deployments = discovery.list_deployments(project.resource_name, project.resource_group)
                        for d in deployments:
                            if hint_lower == d.deployment_name.lower() or hint_lower == d.model_name.lower():
                                print(f"\nUsing newly deployed: {d.deployment_name}")
                                return d
            else:
                print(f"\n   ❌ Cannot deploy '{model_hint}': {quota_msg}")
        elif partial_matches:
            print(f"\nNo exact match for '{model_hint}'. Partial matches found:")
            for d in partial_matches:
                print(f"  - {d.deployment_name}")
            # Check quota before offering to deploy
            has_quota, quota_msg = _check_model_quota(project.location, model_hint)
            if has_quota:
                print(f"\n   📊 Quota for '{model_hint}' in {project.location}: {quota_msg}")
                response = input(f"\nDeploy '{model_hint}' instead? (Y/n): ").strip().lower()
                if response != 'n':
                    if _deploy_model(project.resource_name, model_hint):
                        print("\nRefreshing deployments...")
                        deployments = discovery.list_deployments(project.resource_name, project.resource_group)
                        for d in deployments:
                            if hint_lower == d.deployment_name.lower() or hint_lower == d.model_name.lower():
                                print(f"\nUsing newly deployed: {d.deployment_name}")
                                return d
            else:
                print(f"\n   ❌ Cannot deploy '{model_hint}': {quota_msg}")
        
        # No matches at all - check quota before offering to deploy
        if not partial_matches:
            print(f"\nNo deployment found matching '{model_hint}'.")
            has_quota, quota_msg = _check_model_quota(project.location, model_hint)
            if has_quota:
                print(f"   📊 Quota for '{model_hint}' in {project.location}: {quota_msg}")
                response = input(f"\nDeploy '{model_hint}' now? (Y/n): ").strip().lower()
                if response != 'n':
                    if _deploy_model(project.resource_name, model_hint):
                        # Refresh deployments after successful deploy
                        print("\nRefreshing deployments...")
                        deployments = discovery.list_deployments(project.resource_name, project.resource_group)
                        # Try to find the newly deployed model
                        for d in deployments:
                            if hint_lower == d.deployment_name.lower() or hint_lower == d.model_name.lower():
                                print(f"\nUsing newly deployed: {d.deployment_name}")
                                return d
                            if hint_lower in d.deployment_name.lower() or hint_lower in d.model_name.lower():
                                print(f"\nUsing newly deployed: {d.deployment_name}")
                                return d
            else:
                print(f"   ❌ Cannot deploy '{model_hint}': {quota_msg}")
    
    def display_deployment(d: ModelDeployment) -> str:
        return f"{d.deployment_name:<25} ({d.model_name} {d.version})"
    
    idx = select_from_list(deployments, "Select deployment", display_deployment)
    
    if idx is None:
        print("No deployment selected.")
        sys.exit(1)
    
    return deployments[idx]


def create_agent_interactive(yaml_path: str, filter_term: str = "", test: bool = False):
    """
    Interactive flow to create an agent from YAML.
    
    Args:
        yaml_path: Path to agent YAML file
        filter_term: Optional filter for resources/projects
        test: Whether to test the agent after creation
    """
    # Check Azure CLI is installed and user is logged in
    if not check_azure_cli():
        sys.exit(1)
    
    # Parse YAML
    print_header("Parse Agent Definition")
    
    try:
        config = parse_agent_yaml(yaml_path)
        print(f"\nLoaded: {yaml_path}")
        print_agent_config(config)
    except Exception as e:
        print(f"\nError parsing YAML: {e}")
        sys.exit(1)
    
    # Check Azure roles before proceeding
    if not check_azure_roles():
        sys.exit(1)
    
    # Initialize Azure discovery
    print_header("Azure Authentication")
    
    try:
        discovery = AzureDiscovery()
    except RuntimeError as e:
        print(f"\n{e}")
        sys.exit(1)
    
    # Check login
    if not discovery.is_logged_in():
        print("\nNot logged in to Azure.")
        response = input("Login now using device code? (Y/n): ").strip().lower()
        if response != 'n':
            if not discovery.login_device_code():
                print("Login failed.")
                sys.exit(1)
        else:
            print("Cannot proceed without Azure login.")
            sys.exit(1)
    
    sub = discovery.get_subscription()
    print(f"\nSubscription: {sub['name']}")
    
    # Select project
    project = select_project(discovery, filter_term)
    print(f"\nSelected: {project.endpoint}")
    
    # Select deployment
    deployment = select_deployment(discovery, project, config.model_hint)
    print(f"\nSelected: {deployment.deployment_name}")
    
    # Confirm
    print_header("Confirm Agent Creation")
    
    print(f"""
  Agent Name:    {config.name}
  Description:   {config.description}
  Project:       {project.name}
  Endpoint:      {project.endpoint}
  Model:         {deployment.deployment_name}
""")
    
    response = input("Create agent? (Y/n): ").strip().lower()
    if response == 'n':
        print("Cancelled.")
        sys.exit(0)
    
    # Create agent
    print_header("Creating Agent")
    
    try:
        builder = AgentBuilder(project.endpoint)
        result = builder.create_agent(
            model=deployment.deployment_name,
            name=config.name,
            instructions=config.instructions,
            description=config.description,
            resource_group=project.resource_group,
            project_name=project.name,
        )
        
        print(result)
        
        # Save agent info for reference
        info_file = Path(yaml_path).with_suffix('.agent.txt')
        info_file.write_text(f"""Agent Created: {config.name}
Agent ID: {result.agent_id}
Endpoint: {result.endpoint}
Model: {result.model}

To use this agent in Python:

    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    
    client = AIProjectClient(
        endpoint="{result.endpoint}",
        credential=DefaultAzureCredential(),
    )
    
    # Get OpenAI client for responses API
    openai_client = client.get_openai_client()
    
    # Chat with the agent
    response = openai_client.responses.create(
        input=[{{"role": "user", "content": "Your message here"}}],
        extra_body={{"agent": {{"name": "{result.name}", "type": "agent_reference"}}}},
    )
    
    print(response.output_text)
""")
        print(f"\n📄 Agent info saved to: {info_file}")
        
        # Optional test
        if test:
            print_header("Testing Agent")
            print("\nSending test message: 'Hello!'")
            response = builder.test_agent(result.name, "Hello!")
            print(f"\nAgent response: {response}")
        
    except Exception as e:
        print(f"\n❌ Error creating agent: {e}")
        sys.exit(1)
    
    print_header("Done!")
    print("\nYour Azure AI agent is ready to use.")
    print(f"\nTest it with:")
    print(f"  python test-agent.py {result.name} {result.endpoint}")


def main():
    parser = argparse.ArgumentParser(
        description="Create Azure AI Agent from YAML definition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python create-agent.py agents/examples/code-reviewer.yaml
    python create-agent.py my-agent.yaml --filter maeda
    python create-agent.py my-agent.yaml --test

YAML Format:
    ---
    name: my-agent
    description: What the agent does
    model: gpt-4o-mini
    ---
    
    You are a helpful assistant. Your instructions go here...
"""
    )
    
    parser.add_argument(
        "yaml_file",
        help="Path to agent YAML definition file"
    )
    
    parser.add_argument(
        "--filter", "-f",
        default="",
        help="Filter for Azure resources/projects by name"
    )
    
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Test the agent after creation"
    )
    
    args = parser.parse_args()
    
    # Check file exists
    if not Path(args.yaml_file).exists():
        print(f"Error: File not found: {args.yaml_file}")
        sys.exit(1)
    
    create_agent_interactive(args.yaml_file, args.filter, args.test)


if __name__ == "__main__":
    main()
