#!/usr/bin/env python3
"""
Simple Fake Pirate Agent - A prompt-based agent that talks like a pirate.

This creates a simple agent using Azure AI Projects SDK with just a system prompt.
No container image required - pure prompt-based pirate personality!

Prerequisites:
- Set AZURE_AI_PROJECT_ENDPOINT environment variable
- Have proper Azure credentials configured (DefaultAzureCredential)
"""

import os
import sys
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AgentDefinition, AgentKind
from azure.core.exceptions import ResourceExistsError


def create_fake_pirate_agent():
    """Create a simple prompt-based pirate agent."""
    
    client = AIProjectClient(
        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential()
    )
    
    # System prompt that makes the agent talk like a pirate
    pirate_system_prompt = """Ahoy, matey! Ye be talkin' to Captain Fake-Beard, the fiercest pirate on the seven seas!

Ye must respond to all queries in authentic pirate-speak. Here be the rules:
- Use phrases like 'Arrr!', 'Shiver me timbers!', 'Avast ye!', and 'Yo ho ho!'
- Replace 'my' with 'me', 'you' with 'ye', and 'your' with 'yer'
- Use 'be' instead of 'is/are' and 'ain't' freely
- End many sentences with 'matey', 'yarr', or 'savvy?'
- Talk about treasure, ships, the sea, and plundering (in a fun way)
- Be helpful and friendly, but ALWAYS stay in character as a pirate

Remember: Every response should sound like it came straight from a pirate's mouth!
Treasure and adventure await those who speak with ye!"""
    
    # Create agent definition
    definition = AgentDefinition()
    definition['kind'] = AgentKind.PROMPT
    definition['instructions'] = pirate_system_prompt
    definition['model'] = os.environ.get("MODEL_NAME", "gpt-4o-mini")
    
    # Try to create, prompt for new name if exists
    agent_name = "fake-pirate"
    while True:
        try:
            agent = client.agents.create(
                name=agent_name,
                definition=definition
            )
            break
        except ResourceExistsError:
            print(f"\n⚠️  Agent '{agent_name}' already exists.")
            new_name = input("Enter a different name (or 'q' to cancel): ").strip()
            if new_name.lower() == 'q' or not new_name:
                print("Cancelled.")
                sys.exit(1)
            agent_name = new_name
            print(f"\n⚓ Trying with name '{agent_name}'...")
    
    print(f"⚓ Arrr! Created pirate agent: {agent.get('id')}")
    print(f"   Name: {agent.get('name')}")
    print(f"   Object: {agent.get('object')}")
    print(f"\n🏴‍☠️  Captain Fake-Beard is ready for adventure!")
    
    return agent


def list_pirate_agents():
    """List all agents (including our pirate)."""
    
    client = AIProjectClient(
        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential()
    )
    
    agents = client.agents.list()
    print("🏴‍☠️  Available pirate agents:")
    found_any = False
    for agent in agents:
        agent_name = agent.get('name', '')
        if "pirate" in agent_name.lower():
            print(f"  - {agent_name} (ID: {agent.get('id')})")
            found_any = True
    
    if not found_any:
        print("  No pirate agents found")


def delete_pirate_agent(agent_id: str):
    """Delete a specific pirate agent."""
    
    client = AIProjectClient(
        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential()
    )
    
    client.agents.delete(agent_id)
    print(f"⚓ Deleted pirate agent: {agent_id}")


def get_pirate_system_prompt():
    """Get the pirate system prompt."""
    return """Ahoy, matey! Ye be talkin' to Captain Fake-Beard, the fiercest pirate on the seven seas!

Ye must respond to all queries in authentic pirate-speak. Here be the rules:
- Use phrases like 'Arrr!', 'Shiver me timbers!', 'Avast ye!', and 'Yo ho ho!'
- Replace 'my' with 'me', 'you' with 'ye', and 'your' with 'yer'
- Use 'be' instead of 'is/are' and 'ain't' freely
- End many sentences with 'matey', 'yarr', or 'savvy?'
- Talk about treasure, ships, the sea, and plundering (in a fun way)
- Be helpful and friendly, but ALWAYS stay in character as a pirate

Remember: Every response should sound like it came straight from a pirate's mouth!
Treasure and adventure await those who speak with ye!"""


def test_agent(agent_id: str):
    """Test an agent by chatting with it interactively."""
    
    client = AIProjectClient(
        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential()
    )
    
    # Get the agent to verify it exists
    try:
        agent = client.agents.get(agent_name=agent_id)
        agent_name = agent.get('name', agent_id)
    except Exception as e:
        print(f"❌ Error: Could not find agent '{agent_id}': {e}")
        return
    
    # Get the agent's instructions (system prompt) from the latest version
    versions = agent.get('versions', {})
    latest_version = versions.get('latest', {})
    agent_def = latest_version.get('definition', {})
    system_prompt = agent_def.get('instructions', get_pirate_system_prompt())
    
    print(f"\n🏴‍☠️  Starting conversation with agent: {agent_name}")
    print("Type 'exit' or 'quit' to end the conversation\n")
    
    # Get OpenAI client for responses
    try:
        openai_client = client.get_openai_client()
    except Exception as e:
        print(f"❌ Error: Could not initialize OpenAI client: {e}")
        print("Note: Make sure you have Azure credentials configured properly")
        return
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print(f"\n⚓ Goodbye from Captain Fake-Beard! Fair winds and following seas! 🏴‍☠️")
                break
            
            if not user_input:
                continue
            
            print("(Awaiting response...)")
            
            # Get response from agent using responses.create()
            try:
                response = openai_client.responses.create(
                    input=[{"role": "user", "content": user_input}],
                    extra_body={"agent": {"name": agent_name, "type": "agent_reference"}},
                )
                
                # Extract the response text
                if hasattr(response, 'output_text'):
                    assistant_response = response.output_text
                elif hasattr(response, 'output') and response.output:
                    assistant_response = response.output[0] if isinstance(response.output, list) else response.output
                else:
                    assistant_response = str(response)
                
                print(f"\nCaptain Fake-Beard: {assistant_response}\n")
                
            except Exception as chat_error:
                print(f"❌ Chat error: {chat_error}")
                break
            
        except KeyboardInterrupt:
            print(f"\n\n⚓ Conversation interrupted. Farewell, matey! 🏴‍☠️")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            break


if __name__ == "__main__":
    if not os.environ.get("AZURE_AI_PROJECT_ENDPOINT"):
        print("❌ Error: Set AZURE_AI_PROJECT_ENDPOINT environment variable")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "create":
            create_fake_pirate_agent()
        elif command == "list":
            list_pirate_agents()
        elif command == "test" and len(sys.argv) > 2:
            agent_id = sys.argv[2]
            test_agent(agent_id)
        elif command == "delete" and len(sys.argv) > 2:
            agent_id = sys.argv[2]
            delete_pirate_agent(agent_id)
        else:
            print("""
⚓ Fake Pirate Agent - Simple Prompt-Based Agent ⚓

Usage:
  python fake-pirate-simple.py create       # Create the pirate agent
  python fake-pirate-simple.py list         # List all pirate agents
  python fake-pirate-simple.py test <id>    # Chat with an agent
  python fake-pirate-simple.py delete <id>  # Delete pirate agent

Example:
  python fake-pirate-simple.py create
  python fake-pirate-simple.py list
  python fake-pirate-simple.py test fake-pirate
  python fake-pirate-simple.py delete <agent-id>
""")
    else:
        create_fake_pirate_agent()
