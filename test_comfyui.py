#!/usr/bin/env python3
"""Test script to verify ComfyUI integration"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_comfyui():
    """Test ComfyUI image generation"""
    print("🧪 Testing ComfyUI integration...")
    
    try:
        from src.imagegen.comfyui_client import ComfyUIClient
        print("✅ ComfyUI client imported successfully")
        
        # Initialize client
        client = ComfyUIClient("192.168.4.208:8188")
        print(f"✅ Client initialized for server: {client.server_address}")
        
        # Test server connectivity
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{client.server_address}/", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    print(f"✅ ComfyUI server reachable: {response.status}")
        except Exception as e:
            print(f"❌ ComfyUI server not reachable: {e}")
            return False
        
        # Test workflow loading
        try:
            workflow = client.load_workflow()
            print(f"✅ Workflow loaded: {len(workflow)} nodes")
        except Exception as e:
            print(f"❌ Failed to load workflow: {e}")
            return False
        
        # Test image generation with a simple recipe
        print("🎨 Testing image generation...")
        try:
            image_path = await client.generate_recipe_image(
                "Test Spaghetti Carbonara",
                output_dir="./media",
                filename_prefix="test"
            )
            
            if image_path:
                print(f"✅ Image generated successfully: {image_path}")
                return True
            else:
                print("❌ Image generation returned None")
                return False
                
        except Exception as e:
            print(f"❌ Image generation failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_comfyui())
    if success:
        print("🎉 ComfyUI integration test passed!")
        sys.exit(0)
    else:
        print("💥 ComfyUI integration test failed!")
        sys.exit(1)