#!/usr/bin/env python3
"""
Simple test of Ollama connectivity
"""

import asyncio
import httpx

async def test_simple_generation():
    print("Testing simple generation...")
    
    # Try with the smaller tinyllama model first
    models_to_test = [
        "tinyllama:latest",
        "ALIENTELLIGENCE/recipemaker:latest"
    ]
    
    for model in models_to_test:
        print(f"\n🧪 Testing model: {model}")
        
        simple_prompt = "Create a simple chicken recipe in JSON format with name, ingredients, and instructions."
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://192.168.4.170:11434/api/generate",
                    json={
                        "model": model,
                        "prompt": simple_prompt,
                        "stream": False
                    },
                    timeout=30.0  # Short timeout for test
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ {model} responded successfully")
                    print(f"Response length: {len(result.get('response', ''))}")
                    print(f"Response preview: {result.get('response', '')[:200]}...")
                    
                    # Test if it's valid JSON
                    try:
                        import json
                        json.loads(result['response'])
                        print("✅ Response is valid JSON")
                    except:
                        print("⚠️  Response is not valid JSON")
                        
                else:
                    print(f"❌ {model} failed with status: {response.status_code}")
                    
        except asyncio.TimeoutError:
            print(f"⏰ {model} timed out after 30 seconds")
        except Exception as e:
            print(f"❌ {model} failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_generation())