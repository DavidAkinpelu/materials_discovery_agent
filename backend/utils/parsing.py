import json
from typing import Any, Dict

def parse_json_markdown(text: str) -> Dict[str, Any]:
    """
    Parses a JSON string that might be wrapped in markdown code blocks.
    """
    content = text.strip()
    
    # Handle standard markdown json block
    if content.startswith("```json"):
        content = content[7:] # Strip ```json
    elif content.startswith("```"):
        content = content[3:] # Strip ```
        
    if content.endswith("```"):
        content = content[:-3] # Strip ```
        
    content = content.strip()
    
    return json.loads(content)
