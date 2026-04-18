import os

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")

import aiofiles

async def load_prompt(filename: str) -> str:
    filepath = os.path.join(PROMPTS_DIR, filename)
    async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
        content = await f.read()
        return content.strip()
