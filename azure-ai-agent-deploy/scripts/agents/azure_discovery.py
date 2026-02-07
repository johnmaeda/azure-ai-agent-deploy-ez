"""
Azure Discovery Module

Discovers Azure AI resources, projects, and deployments using az CLI.
Replicates shell script logic in Python for programmatic use.
"""

import json
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class AzureResource:
    """Azure AI resource (Cognitive Services account)."""
    name: str
    resource_group: str
    location: str
    
    @property
    def endpoint(self) -> str:
        return f"https://{self.name}.cognitiveservices.azure.com/"


@dataclass
class AzureProject:
    """Azure AI Foundry project."""
    name: str
    resource_name: str
    resource_group: str
    location: str
    
    @property
    def endpoint(self) -> str:
        return f"https://{self.resource_name}.services.ai.azure.com/api/projects/{self.name}"


@dataclass 
class ModelDeployment:
    """Deployed model in Azure AI resource."""
    deployment_name: str
    model_name: str
    version: str


class AzureDiscovery:
    """Discover Azure AI resources using az CLI."""
    
    def __init__(self):
        self._check_cli()
    
    def _check_cli(self):
        """Check if az CLI is available."""
        result = subprocess.run(["az", "--version"], capture_output=True)
        if result.returncode != 0:
            raise RuntimeError("Azure CLI (az) not found. Install from: https://aka.ms/installazurecli")
    
    def _run_az(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run az CLI command."""
        cmd = ["az"] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        if check and result.returncode != 0:
            raise RuntimeError(f"az command failed: {result.stderr}")
        return result
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in to Azure."""
        result = self._run_az(["account", "show"], check=False)
        return result.returncode == 0
    
    def login_device_code(self) -> bool:
        """
        Login using device code flow.
        Returns True if login successful.
        """
        print("\n🔐 Azure Login Required")
        print("=" * 50)
        print("Starting device code authentication...")
        print("A code will be displayed - enter it at the URL shown.\n")
        
        # Run login with device code - this outputs to terminal
        result = subprocess.run(
            ["az", "login", "--use-device-code"],
            # Don't capture output so user sees the device code
        )
        
        return result.returncode == 0
    
    def ensure_logged_in(self) -> bool:
        """Ensure user is logged in, prompting if needed."""
        if self.is_logged_in():
            return True
        
        print("Not logged in to Azure.")
        response = input("Login now? (y/N): ").strip().lower()
        if response == 'y':
            return self.login_device_code()
        return False
    
    def get_subscription(self) -> dict:
        """Get current subscription info."""
        result = self._run_az([
            "account", "show",
            "--query", "{name:name, id:id}",
            "-o", "json"
        ])
        return json.loads(result.stdout)
    
    def list_resources(self, filter_term: str = "") -> list[AzureResource]:
        """
        List Azure AI resources (CognitiveServices accounts).
        
        Args:
            filter_term: Optional filter for resource name or resource group
            
        Returns:
            List of AzureResource objects
        """
        result = self._run_az([
            "resource", "list",
            "--resource-type", "Microsoft.CognitiveServices/accounts",
            "--query", "[].{name:name, rg:resourceGroup, loc:location}",
            "-o", "json"
        ])
        
        resources_data = json.loads(result.stdout)
        resources = []
        
        for r in resources_data:
            # Apply filter
            if filter_term:
                if filter_term.lower() not in r["name"].lower() and \
                   filter_term.lower() not in r["rg"].lower():
                    continue
            
            resources.append(AzureResource(
                name=r["name"],
                resource_group=r["rg"],
                location=r["loc"]
            ))
        
        return resources
    
    def list_projects(self, filter_term: str = "") -> list[AzureProject]:
        """
        List Azure AI Foundry projects.
        
        Args:
            filter_term: Optional filter for project/resource name
            
        Returns:
            List of AzureProject objects
        """
        result = self._run_az([
            "resource", "list",
            "--resource-type", "Microsoft.CognitiveServices/accounts/projects",
            "--query", "[].{fullName:name, rg:resourceGroup, loc:location}",
            "-o", "json"
        ])
        
        projects_data = json.loads(result.stdout)
        projects = []
        
        for p in projects_data:
            # fullName is "resource/project"
            parts = p["fullName"].split("/")
            if len(parts) != 2:
                continue
            
            resource_name, project_name = parts
            
            # Apply filter
            if filter_term:
                if filter_term.lower() not in resource_name.lower() and \
                   filter_term.lower() not in project_name.lower() and \
                   filter_term.lower() not in p["rg"].lower():
                    continue
            
            projects.append(AzureProject(
                name=project_name,
                resource_name=resource_name,
                resource_group=p["rg"],
                location=p["loc"]
            ))
        
        return projects
    
    def list_deployments(self, resource_name: str, resource_group: str) -> list[ModelDeployment]:
        """
        List model deployments in a resource.
        
        Args:
            resource_name: Name of the CognitiveServices account
            resource_group: Resource group name
            
        Returns:
            List of ModelDeployment objects
        """
        result = self._run_az([
            "cognitiveservices", "account", "deployment", "list",
            "--name", resource_name,
            "--resource-group", resource_group,
            "--query", "[].{name:name, model:properties.model.name, version:properties.model.version}",
            "-o", "json"
        ], check=False)
        
        if result.returncode != 0:
            return []
        
        deployments_data = json.loads(result.stdout or "[]")
        deployments = []
        
        for d in deployments_data:
            deployments.append(ModelDeployment(
                deployment_name=d["name"],
                model_name=d["model"] or "",
                version=d["version"] or ""
            ))
        
        return deployments
    
    def get_api_key(self, resource_name: str, resource_group: str) -> Optional[str]:
        """Get API key for a resource."""
        result = self._run_az([
            "cognitiveservices", "account", "keys", "list",
            "-n", resource_name,
            "-g", resource_group,
            "--query", "key1",
            "-o", "tsv"
        ], check=False)
        
        if result.returncode == 0:
            return result.stdout.strip()
        return None


def select_from_list(items: list, prompt: str, display_fn=str) -> Optional[int]:
    """
    Display numbered list and get user selection.
    
    Args:
        items: List of items to choose from
        prompt: Prompt text
        display_fn: Function to convert item to display string
        
    Returns:
        Selected index (0-based) or None if cancelled
    """
    if not items:
        return None
    
    print()
    for i, item in enumerate(items, 1):
        print(f"  [{i:2d}] {display_fn(item)}")
    print()
    
    if len(items) == 1:
        print("Auto-selecting the only option...")
        return 0
    
    try:
        choice = input(f"{prompt} (1-{len(items)}): ").strip()
        idx = int(choice) - 1
        if 0 <= idx < len(items):
            return idx
    except (ValueError, KeyboardInterrupt):
        pass
    
    return None


if __name__ == "__main__":
    # Test discovery
    discovery = AzureDiscovery()
    
    if not discovery.ensure_logged_in():
        print("Not logged in.")
        exit(1)
    
    print(f"\nSubscription: {discovery.get_subscription()['name']}")
    
    resources = discovery.list_resources("maeda")
    print(f"\nFound {len(resources)} resources:")
    for r in resources:
        print(f"  - {r.name} ({r.location})")
