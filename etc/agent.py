"""
Azure AI Foundry Agent Example

This script demonstrates how to create and run an AI agent using the Azure AI Projects SDK.
The agent uses the Code Interpreter tool to help with math questions and visualizations.

Prerequisites:
- Set environment variable AZURE_API_KEY to your Azure OpenAI API key
- OR run 'az login' to authenticate with Azure
"""

from pathlib import Path
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import CodeInterpreterTool

# Configuration - Replace with your Azure AI project endpoint
PROJECT_ENDPOINT = "https://<resource-name>.services.ai.azure.com/api/projects/<project-name>"
MODEL_DEPLOYMENT_NAME = "gpt-4o-mini"


def main():
    # Azure AI Agents API requires TokenCredential (not AzureKeyCredential)
    # Use DefaultAzureCredential which works with 'az login'
    credential = DefaultAzureCredential()
    print("Using DefaultAzureCredential (az login)")

    project_client = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=credential,
    )

    with project_client:
        # Set up the Code Interpreter tool
        code_interpreter = CodeInterpreterTool()

        # Create the agent
        agent = project_client.agents.create_agent(
            model=MODEL_DEPLOYMENT_NAME,
            name="my-agent",
            instructions="""You politely help with math questions. 
            Use the Code Interpreter tool when asked to visualize numbers.""",
            tools=code_interpreter.definitions,
            tool_resources=code_interpreter.resources,
        )
        print(f"Created agent, ID: {agent.id}")

        # Create a thread for communication
        thread = project_client.agents.threads.create()
        print(f"Created thread, ID: {thread.id}")

        # Define the question
        question = """Draw a graph for a line with a slope of 4 
        and y-intercept of 9 and provide the file to me?"""

        # Add a message to the thread
        message = project_client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=question,
        )
        print(f"Created message, ID: {message['id']}")

        # Create and process an agent run
        run = project_client.agents.runs.create_and_process(
            thread_id=thread.id,
            agent_id=agent.id,
            additional_instructions="""Please address the user as Jane Doe.
            The user has a premium account.""",
        )

        print(f"Run finished with status: {run.status}")

        # Check if the run failed
        if run.status == "failed":
            print(f"Run failed: {run.last_error}")
            return

        # Fetch and log all messages
        messages = project_client.agents.messages.list(thread_id=thread.id)
        print(f"Messages: {messages}")

        for message in messages:
            print(f"Role: {message.role}, Content: {message.content}")
            for this_content in message.content:
                print(f"Content Type: {this_content.type}, Content Data: {this_content}")
                if hasattr(this_content, 'text') and this_content.text.annotations:
                    for annotation in this_content.text.annotations:
                        print(f"Annotation Type: {annotation.type}, Text: {annotation.text}")
                        print(f"Start Index: {annotation.start_index}")
                        print(f"End Index: {annotation.end_index}")
                        print(f"File ID: {annotation.file_path.file_id}")
                        # Save every image file in the message
                        file_id = annotation.file_path.file_id
                        file_name = f"{file_id}_image_file.png"
                        project_client.agents.files.save(file_id=file_id, file_name=file_name)
                        print(f"Saved image file to: {Path.cwd() / file_name}")

        # Uncomment these lines to delete the agent when done
        # project_client.agents.delete_agent(agent.id)
        # print("Deleted agent")


if __name__ == "__main__":
    main()
