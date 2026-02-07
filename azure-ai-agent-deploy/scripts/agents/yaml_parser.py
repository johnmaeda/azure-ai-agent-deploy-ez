"""
YAML Parser for Agent Definitions

Parses YAML frontmatter format for prompt-based agents:
---
name: my-agent
description: A helpful assistant
model: gpt-4o-mini
---

You are a helpful assistant. When invoked...
"""

import re
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML not installed. Run: pip install pyyaml")
    raise


@dataclass
class AgentConfig:
    """Parsed agent configuration."""
    name: str
    description: str
    instructions: str
    model_hint: Optional[str] = None
    
    def __str__(self) -> str:
        return f"""Agent: {self.name}
Description: {self.description}
Model: {self.model_hint or 'default'}
Instructions: {self.instructions[:100]}..."""


def parse_agent_yaml(file_path: str | Path) -> AgentConfig:
    """
    Parse an agent YAML file with frontmatter.
    
    Format:
        ---
        name: agent-name
        description: What the agent does
        model: gpt-4o-mini   # optional
        ---
        
        Instructions content here...
    
    Args:
        file_path: Path to the YAML file
        
    Returns:
        AgentConfig with parsed values
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Agent file not found: {file_path}")
    
    content = file_path.read_text()
    
    # Parse frontmatter (content between --- markers)
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n?(.*)'
    match = re.match(frontmatter_pattern, content, re.DOTALL)
    
    if not match:
        raise ValueError(f"Invalid agent file format. Expected YAML frontmatter between --- markers.")
    
    frontmatter_str = match.group(1)
    instructions = match.group(2).strip()
    
    # Parse YAML frontmatter
    try:
        frontmatter = yaml.safe_load(frontmatter_str)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in frontmatter: {e}")
    
    if not isinstance(frontmatter, dict):
        raise ValueError("Frontmatter must be a YAML dictionary")
    
    # Extract required fields
    name = frontmatter.get("name")
    if not name:
        raise ValueError("Agent must have a 'name' field")
    
    description = frontmatter.get("description", "")
    model_hint = frontmatter.get("model")
    
    return AgentConfig(
        name=name,
        description=description,
        instructions=instructions,
        model_hint=model_hint,
    )


def parse_agent_string(content: str) -> AgentConfig:
    """
    Parse agent definition from a string.
    
    Args:
        content: YAML frontmatter string
        
    Returns:
        AgentConfig with parsed values
    """
    # Write to temp and parse
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    try:
        return parse_agent_yaml(temp_path)
    finally:
        Path(temp_path).unlink()


if __name__ == "__main__":
    # Test with sample
    sample = """---
name: code-reviewer
description: Reviews code for quality and best practices
model: gpt-4o-mini
---

You are a code reviewer. When invoked, analyze the code and provide
specific, actionable feedback on quality, security, and best practices.
"""
    config = parse_agent_string(sample)
    print(config)
