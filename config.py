import os
import ast
from typing import List
from dotenv import load_dotenv

load_dotenv()

def parse_admin_ids(value: str) -> List[int]:
    """Parse ADMIN_IDS from environment variable.
    
    Supports two formats:
    1. Comma-separated: "123,456,789"
    2. String representation of list: "['123', '456', '789']" or "[123, 456, 789]"
    """
    if not value:
        return []
    
    # Try to parse as Python literal first (handles list format)
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, list):
            return [int(i) for i in parsed if i]
    except (ValueError, SyntaxError):
        pass
    
    # Fall back to comma-separated format
    return [int(i) for i in value.split(",") if i]

class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///shop.db")
    ADMIN_IDS: List[int] = parse_admin_ids(os.getenv("ADMIN_IDS", ""))
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

config = Config()
