import re
import json
from typing import Optional

def extract_code_block(text: str, language: str = "") -> str:
    """
    Extracts the content of a markdown code block from the given text.
    If language is provided, it specifically looks for blocks like ```language
    
    If NO code block is found, it returns an empty string instead of the whole text.
    """
    # Pattern to match ```[language]\n[code]\n```
    if language:
        pattern = rf"```(?:{language})\n?(.*?)\n?```"
    else:
        pattern = r"```(?:\w+)?\n?(.*?)\n?```"
    
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return matches[0].strip()
    
    # Strictly return empty string if no valid block is found to prevent garbage inputs
    return ""

def parse_json_flexible(text: str) -> dict:
    """
    Tries to find and parse a JSON object within a string that might contain noise.
    """
    try:
        # First try direct parse
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find something that looks like a JSON object
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
    return {}
