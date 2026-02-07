#!/usr/bin/env python3
"""
Test an Azure AI Agent interactively.

Usage:
    python test-agent.py <agent-name> <endpoint>
    python test-agent.py math-tutor https://myresource.services.ai.azure.com/api/projects/myproject

Or use the .agent.txt file:
    python test-agent.py agents/examples/math-tutor.agent.txt
"""

import sys
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


def parse_agent_file(file_path: str) -> tuple[str, str]:
    """
    Parse an .agent.txt file to extract agent name and endpoint.
    
    Returns:
        (agent_name, endpoint)
    """
    content = Path(file_path).read_text()
    
    agent_name = None
    endpoint = None
    
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("Agent ID:"):
            agent_name = line.split(":", 1)[1].strip()
        elif line.startswith("Endpoint:"):
            endpoint = line.split(":", 1)[1].strip()
    
    if not agent_name or not endpoint:
        raise ValueError(f"Could not parse agent name and endpoint from {file_path}")
    
    return agent_name, endpoint


def print_code_sample(agent_name: str, endpoint: str):
    """Print Python code to replicate the chat."""
    print("\n" + "=" * 60)
    print(" Code to replicate this chat")
    print("=" * 60)
    print("""
# Install requirements:
#   pip install azure-ai-projects azure-identity

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Connect to Azure AI project
client = AIProjectClient(
    endpoint=\"""" + endpoint + """\",
    credential=DefaultAzureCredential()
)

# Get OpenAI client for the responses API
openai_client = client.get_openai_client()

# Chat with the agent
response = openai_client.responses.create(
    input=[{"role": "user", "content": "Your message here"}],
    extra_body={"agent": {"name": \"""" + agent_name + """\", "type": "agent_reference"}},
)

print(response.output_text)
""")


def test_agent(agent_name: str, endpoint: str):
    """Test an agent by chatting with it interactively."""
    
    print(f"\n🤖 Connecting to agent '{agent_name}'...")
    print(f"   Endpoint: {endpoint}")
    
    client = AIProjectClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential()
    )
    
    # Verify agent exists
    try:
        agent = client.agents.get(agent_name=agent_name)
        print(f"   ✅ Agent found: {agent.get('name')}")
    except Exception as e:
        print(f"\n❌ Error: Could not find agent '{agent_name}': {e}")
        return
    
    # Get OpenAI client for responses
    try:
        openai_client = client.get_openai_client()
    except Exception as e:
        print(f"\n❌ Error: Could not initialize OpenAI client: {e}")
        return
    
    print(f"\n💬 Starting conversation with '{agent_name}'")
    print("   Type 'exit' or 'quit' to end, Ctrl+C to interrupt\n")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Get response from agent
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
                
                print(f"\n{agent_name}: {assistant_response}")
                
            except Exception as chat_error:
                print(f"\n❌ Chat error: {chat_error}")
                break
            
        except KeyboardInterrupt:
            print("\n\n👋 Conversation interrupted. Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break
    
    # Print code sample after chat ends
    print_code_sample(agent_name, endpoint)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nExamples:")
        print("  python test-agent.py math-tutor https://myresource.services.ai.azure.com/api/projects/myproject")
        print("  python test-agent.py agents/examples/math-tutor.agent.txt")
        sys.exit(1)
    
    # Check if first arg is a file
    if len(sys.argv) == 2 and Path(sys.argv[1]).exists():
        file_path = sys.argv[1]
        try:
            agent_name, endpoint = parse_agent_file(file_path)
            print(f"📄 Loaded from: {file_path}")
        except Exception as e:
            print(f"❌ Error parsing file: {e}")
            sys.exit(1)
    elif len(sys.argv) >= 3:
        agent_name = sys.argv[1]
        endpoint = sys.argv[2]
    else:
        print("❌ Error: Provide either an .agent.txt file or agent-name + endpoint")
        print(__doc__)
        sys.exit(1)
    
    test_agent(agent_name, endpoint)


if __name__ == "__main__":
    main()
