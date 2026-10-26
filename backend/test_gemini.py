import asyncio
import os
from app.core.gemini_client import gemini_client
from app.core.config import settings

async def main():
    print("=" * 60)
    print("Testing Google Gemini Brain (AI Study Buddy System)")
    print("=" * 60)
    
    health = await gemini_client.check_health()
    print("1. Health Status:", health)
    
    if health.get("status") == "connected":
        print("\n2. Testing quick generation...")
        res = await gemini_client.generate("Explain the Chain Rule in backpropagation in 2 sentences.")
        print("Response:\n", res)
    else:
        print("\nNote: GEMINI_API_KEY is currently unconfigured or needs a valid key in backend/.env")
        print("To activate: Get an API key from Google AI Studio (https://aistudio.google.com/)")
        print("and set GEMINI_API_KEY=\"AIza...\" in backend/.env")

if __name__ == "__main__":
    asyncio.run(main())
