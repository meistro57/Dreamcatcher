#!/usr/bin/env python3
"""
Quick test script for OpenRouter integration
Run this to verify OpenRouter is working correctly
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from services.ai_service import AIService


async def test_openrouter():
    """Test OpenRouter integration"""
    print("🧪 Testing OpenRouter Integration\n")

    # Initialize AI service
    ai_service = AIService()

    # Check if OpenRouter is available
    print("📊 Service Status:")
    print(f"  - Claude available: {ai_service.claude_client is not None}")
    print(f"  - OpenAI available: {ai_service.openai_client is not None}")
    print(f"  - OpenRouter available: {ai_service.openrouter_client is not None}")
    print()

    if not ai_service.openrouter_client:
        print("⚠️  OpenRouter client not initialized")
        print("   Please set OPENROUTER_API_KEY in your .env file")
        print("   Get your API key from: https://openrouter.ai/keys")
        return False

    # Get available models
    print("🎯 Available Models:")
    models = ai_service.get_available_models()
    openrouter_models = [m for m in models if m.startswith("openrouter/")]
    for model in openrouter_models:
        print(f"  - {model}")
    print()

    # Test simple generation
    print("🚀 Testing generation with OpenRouter...")
    try:
        response = await ai_service.generate_response(
            prompt="Say 'Hello from OpenRouter!' in a creative way.",
            model="openrouter/anthropic/claude-3-haiku",
            max_tokens=50
        )

        print("✅ Success!")
        print(f"  Model: {response.model}")
        print(f"  Response: {response.response}")
        print(f"  Tokens: {response.tokens_used}")
        print(f"  Time: {response.response_time:.2f}s")
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    # Test fallback
    print("🔄 Testing fallback mechanism...")
    try:
        # Try to use a model that might not be available
        response = await ai_service.generate_response(
            prompt="Test fallback",
            model="openrouter/meta-llama/llama-3-70b-instruct",
            max_tokens=20
        )

        print(f"✅ Fallback test: {response.model}")
        if response.fallback_used:
            print(f"  ⚠️  Fallback was used (original: {response.original_model})")
        print()

    except Exception as e:
        print(f"⚠️  Fallback test error (expected if quota limited): {e}")
        print()

    # Show usage stats
    print("📈 Usage Statistics:")
    stats = ai_service.get_usage_stats()
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  OpenRouter requests: {stats['openrouter_requests']}")
    print(f"  Success rate: {stats['success_rate']:.1%}")
    print()

    print("✅ OpenRouter integration test complete!")
    return True


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Run test
    result = asyncio.run(test_openrouter())
    sys.exit(0 if result else 1)
