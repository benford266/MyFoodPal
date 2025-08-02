#!/usr/bin/env python3
"""Test script to verify image serving"""

import asyncio
import aiohttp
import os

async def test_image_serving():
    """Test if images are accessible via HTTP"""
    print("🧪 Testing image serving...")
    
    # Check if media directory exists and has files
    media_dir = "./media"
    if not os.path.exists(media_dir):
        print(f"❌ Media directory doesn't exist: {media_dir}")
        return False
    
    # List files in media directory
    files = os.listdir(media_dir)
    image_files = [f for f in files if f.endswith(('.png', '.jpg', '.jpeg'))]
    
    if not image_files:
        print(f"❌ No image files found in {media_dir}")
        return False
    
    print(f"✅ Found {len(image_files)} image files:")
    for f in image_files:
        print(f"   - {f}")
    
    # Test HTTP access to first image
    test_image = image_files[0]
    test_urls = [
        f"http://localhost:8080/media/{test_image}",
        f"http://127.0.0.1:8080/media/{test_image}",
    ]
    
    for url in test_urls:
        try:
            print(f"🔍 Testing URL: {url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', 'unknown')
                        content_length = response.headers.get('content-length', 'unknown')
                        print(f"✅ Image accessible: {response.status}, type: {content_type}, size: {content_length}")
                        return True
                    else:
                        print(f"❌ HTTP error: {response.status}")
        except Exception as e:
            print(f"❌ Connection error: {e}")
    
    return False

if __name__ == "__main__":
    success = asyncio.run(test_image_serving())
    if success:
        print("🎉 Image serving test passed!")
    else:
        print("💥 Image serving test failed!")
        print("💡 Make sure FoodPal is running on localhost:8080")