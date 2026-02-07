#!/usr/bin/env python3
"""
Fake Pirate Agent - A simple hosted agent that talks like a pirate.

This creates a hosted agent using Azure AI Projects SDK.
The agent responds to all queries in pirate-speak.

Prerequisites:
- Set AZURE_AI_PROJECT_ENDPOINT environment variable
- Build and push a container image to ACR with pirate personality
- Grant AcrPull role to your project's managed identity

Note: The hosted agent API (create_version, list_versions, delete_version) 
requires azure-ai-projects>=2.0.0b4 or later. Currently installed is 2.0.0b3.
"""

import os
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


def create_fake_pirate_agent():
    """Create a hosted agent that talks like a pirate."""
    
    print("❌ Error: Hosted agent API (create_version) is not available in azure-ai-projects 2.0.0b3")
    print("   Please upgrade to azure-ai-projects>=2.0.0b4 when it becomes available.")
    print("\n   This function requires:")
    print("   - client.agents.create_version() method")
    print("   - ImageBasedHostedAgentDefinition support")
    return None


def list_pirate_versions():
    """List all versions of the fake-pirate agent."""
    
    print("❌ Error: Hosted agent API (list_versions) is not available in azure-ai-projects 2.0.0b3")
    print("   Please upgrade to azure-ai-projects>=2.0.0b4 when it becomes available.")


def delete_pirate_agent(version: str):
    """Delete a specific version of the fake-pirate agent."""
    
    print("❌ Error: Hosted agent API (delete_version) is not available in azure-ai-projects 2.0.0b3")
    print("   Please upgrade to azure-ai-projects>=2.0.0b4 when it becomes available.")


if __name__ == "__main__":
    import sys
    
    if not os.environ.get("AZURE_AI_PROJECT_ENDPOINT"):
        print("❌ Error: Set AZURE_AI_PROJECT_ENDPOINT environment variable")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "list":
            list_pirate_versions()
        elif command == "delete" and len(sys.argv) > 2:
            delete_pirate_agent(sys.argv[2])
        else:
            print("Usage: python fake-pirate-agent.py [list|delete <version>]")
    else:
        create_fake_pirate_agent()
