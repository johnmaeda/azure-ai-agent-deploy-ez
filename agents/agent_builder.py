"""
Agent Builder Module - Azure AI Projects SDK

Creates Azure AI Foundry agents using the azure-ai-projects SDK.
Uses prompt-based agents with AgentDefinition and AgentKind.PROMPT.
"""

from dataclasses import dataclass
from typing import Optional

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AgentDefinition, AgentKind
from azure.core.exceptions import ResourceExistsError


@dataclass
class CreatedAgent:
    """Result of agent creation."""
    agent_id: str
    name: str
    model: str
    endpoint: str
    resource_group: str = ""
    project_name: str = ""
    
    def __str__(self) -> str:
        lines = [
            "",
            "=== Agent Created Successfully ===",
            f"Agent ID: {self.agent_id}",
            f"Name: {self.name}",
            f"Model: {self.model}",
        ]
        if self.resource_group:
            lines.append(f"Resource Group: {self.resource_group}")
        if self.project_name:
            lines.append(f"Project: {self.project_name}")
        lines.append(f"Endpoint: {self.endpoint}")
        return "\n".join(lines)


class AgentBuilder:
    """Build and manage Azure AI agents using the azure-ai-projects SDK."""
    
    def __init__(self, endpoint: str):
        """
        Initialize agent builder.
        
        Args:
            endpoint: Project endpoint URL
                e.g., "https://resource.services.ai.azure.com/api/projects/project"
        """
        self.endpoint = endpoint.rstrip("/")
        self.credential = DefaultAzureCredential()
        self._client = None
    
    def _get_client(self) -> AIProjectClient:
        """Get or create the AIProjectClient."""
        if self._client is None:
            self._client = AIProjectClient(
                credential=self.credential,
                endpoint=self.endpoint,
            )
        return self._client
    
    def create_agent(
        self,
        model: str,
        name: str,
        instructions: str,
        description: str = "",
        resource_group: str = "",
        project_name: str = "",
        **kwargs,
    ) -> CreatedAgent:
        """
        Create an Azure AI prompt-based agent using the SDK.
        
        Args:
            model: Model deployment name (e.g., "gpt-4o-mini")
            name: Agent name
            instructions: System instructions for the agent
            description: Optional description
            resource_group: Optional resource group name for display
            project_name: Optional project name for display
            
        Returns:
            CreatedAgent with agent details
        """
        print(f"\n📦 Creating agent '{name}'...")
        print(f"   Model: {model}")
        
        client = self._get_client()
        
        # Build agent definition for prompt-based agent
        definition = AgentDefinition()
        definition['kind'] = AgentKind.PROMPT
        definition['instructions'] = instructions
        definition['model'] = model
        
        # Try to create the agent, prompt for new name if exists
        current_name = name
        while True:
            try:
                agent = client.agents.create(
                    name=current_name,
                    definition=definition
                )
                break
            except ResourceExistsError:
                print(f"\n⚠️  Agent '{current_name}' already exists.")
                new_name = input("Enter a different name (or 'q' to cancel): ").strip()
                if new_name.lower() == 'q' or not new_name:
                    raise RuntimeError(f"Agent creation cancelled - name '{current_name}' already exists.")
                current_name = new_name
                print(f"\n📦 Trying with name '{current_name}'...")
                # Force fresh client to avoid any SDK caching issues
                self._client = None
                client = self._get_client()
        
        # Verify the agent was actually created
        try:
            verified = client.agents.get(agent_name=current_name)
            if not verified or not verified.get('id'):
                raise RuntimeError(f"Agent '{current_name}' creation could not be verified")
            print(f"\n✅ Verified agent '{current_name}' exists")
        except Exception as e:
            raise RuntimeError(f"Agent '{current_name}' was not created: {e}")
        
        return CreatedAgent(
            agent_id=agent.get('id'),
            name=agent.get('name', current_name),
            model=model,
            endpoint=self.endpoint,
            resource_group=resource_group,
            project_name=project_name,
        )
    
    def list_agents(self) -> list[dict]:
        """List existing agents."""
        client = self._get_client()
        
        try:
            agents = client.agents.list()
            return [{"id": a.get('id'), "name": a.get('name'), "model": a.get('model')} for a in agents]
        except Exception as e:
            print(f"Warning: Could not list agents: {e}")
            return []
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent by ID."""
        client = self._get_client()
        
        try:
            client.agents.delete(agent_id)
            return True
        except Exception as e:
            print(f"Warning: Could not delete agent: {e}")
            return False
    
    def test_agent(self, agent_name: str, message: str = "Hello!") -> Optional[str]:
        """
        Send a test message to an agent using the responses API.
        
        Args:
            agent_name: Agent name (not ID)
            message: Test message to send
            
        Returns:
            Agent response or None if failed
        """
        client = self._get_client()
        
        try:
            # Get OpenAI client for responses
            openai_client = client.get_openai_client()
            
            # Use responses.create with agent reference
            response = openai_client.responses.create(
                input=[{"role": "user", "content": message}],
                extra_body={"agent": {"name": agent_name, "type": "agent_reference"}},
            )
            
            # Extract the response text
            if hasattr(response, 'output_text'):
                return response.output_text
            elif hasattr(response, 'output') and response.output:
                return response.output[0] if isinstance(response.output, list) else str(response.output)
            else:
                return str(response)
                
        except Exception as e:
            return f"Error: {e}"


if __name__ == "__main__":
    import os
    
    endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "")
    if not endpoint:
        print("Set AZURE_AI_PROJECT_ENDPOINT environment variable")
        exit(1)
    
    builder = AgentBuilder(endpoint)
    
    # Create a test agent
    result = builder.create_agent(
        model="gpt-4o-mini",
        name="test-agent",
        instructions="You are a helpful assistant.",
    )
    
    print(result)
    
    # Test the agent
    print("\n🧪 Testing agent...")
    response = builder.test_agent(result.name, "Hello! What can you help me with?")
    print(f"Response: {response}")
