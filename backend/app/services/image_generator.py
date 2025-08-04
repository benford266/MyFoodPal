"""
Image Generation Service using ComfyUI
"""
import aiohttp
import asyncio
import json
import os
from typing import Optional
from ..config import settings


class ImageGeneratorService:
    """Service for generating recipe images using ComfyUI"""
    
    def __init__(self, server_address: str = None):
        self.server_address = server_address or settings.COMFYUI_SERVER
        self.base_url = f"http://{self.server_address}"
    
    async def generate_recipe_image(self, 
                                  recipe_name: str, 
                                  output_dir: str = "./media",
                                  filename_prefix: str = "recipe") -> Optional[str]:
        """
        Generate an image for a recipe
        
        Args:
            recipe_name: Name of the recipe to generate image for
            output_dir: Directory to save the image
            filename_prefix: Prefix for the generated filename
            
        Returns:
            Path to the generated image file, or None if generation failed
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Simple prompt for food image generation
            prompt = f"A professional food photography of {recipe_name}, appetizing, well-lit, restaurant quality, detailed, high resolution"
            
            # For now, return None to indicate image generation is not implemented
            # This is a placeholder for actual ComfyUI integration
            print(f"Image generation requested for: {recipe_name}")
            print(f"Prompt: {prompt}")
            print("Note: ComfyUI integration not fully implemented yet")
            
            return None
            
        except Exception as e:
            print(f"Error generating image for {recipe_name}: {str(e)}")
            return None
    
    async def test_connection(self) -> bool:
        """Test connection to ComfyUI server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    return response.status == 200
        except Exception as e:
            print(f"ComfyUI connection test failed: {str(e)}")
            return False