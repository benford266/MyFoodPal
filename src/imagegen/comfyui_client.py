import json
import uuid
import urllib.request
import urllib.parse
import websocket
import asyncio
import aiohttp
import aiofiles
import os
from typing import Dict, List, Optional, Any
from pathlib import Path


class ComfyUIClient:
    """Client for generating images using ComfyUI API"""
    
    def __init__(self, server_address: str = "192.168.4.208:8188"):
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        self.workflow_path = Path(__file__).parent / "FoodGenerator.json"
        
    def load_workflow(self) -> Dict[str, Any]:
        """Load the ComfyUI workflow JSON"""
        try:
            with open(self.workflow_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Workflow file not found: {self.workflow_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in workflow file: {self.workflow_path}")
    
    async def queue_prompt(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a prompt to ComfyUI"""
        data = {"prompt": prompt, "client_id": self.client_id}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{self.server_address}/prompt",
                json=data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"ComfyUI API error: {response.status}")
    
    async def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """Get generation history for a prompt"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://{self.server_address}/history/{prompt_id}",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get history: {response.status}")
    
    async def get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        """Download generated image"""
        params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url = f"http://{self.server_address}/view?" + urllib.parse.urlencode(params)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(f"Failed to download image: {response.status}")
    
    async def monitor_progress_websocket(self, prompt_id: str) -> bool:
        """Monitor generation progress via WebSocket"""
        try:
            uri = f"ws://{self.server_address}/ws?clientId={self.client_id}"
            
            # Use a timeout for the connection
            async def connect_with_timeout():
                import websockets
                return await websockets.connect(uri)
            
            # Wait for connection with timeout
            websocket_conn = await asyncio.wait_for(connect_with_timeout(), timeout=10.0)
            
            try:
                while True:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket_conn.recv(), timeout=120.0)
                    
                    if isinstance(message, str):
                        data = json.loads(message)
                        if data.get('type') == 'executing':
                            exec_data = data.get('data', {})
                            if exec_data.get('prompt_id') == prompt_id:
                                if exec_data.get('node') is None:
                                    # Generation complete
                                    return True
                                else:
                                    print(f"Executing node: {exec_data.get('node')}")
            finally:
                await websocket_conn.close()
                
        except asyncio.TimeoutError:
            print("WebSocket monitoring timed out")
            return False
        except Exception as e:
            print(f"WebSocket error: {e}")
            return False
    
    async def generate_recipe_image(
        self, 
        recipe_name: str, 
        output_dir: str = "/Users/ben/Code/FoodPal/media",
        filename_prefix: str = None
    ) -> Optional[str]:
        """
        Generate an image for a recipe
        
        Args:
            recipe_name: Name of the recipe to generate image for
            output_dir: Directory to save the image
            filename_prefix: Optional prefix for the saved filename
            
        Returns:
            Path to the saved image file, or None if generation failed
        """
        try:
            # Load and modify workflow
            workflow = self.load_workflow()
            
            # Update the prompt text with recipe name
            recipe_prompt = f"Plate of food on a table in the kitchen, the meal is called, {recipe_name}"
            workflow["6"]["inputs"]["text"] = recipe_prompt
            
            # Generate a random seed for variety
            import random
            workflow["3"]["inputs"]["seed"] = random.randint(1000000, 9999999999)
            
            # Set filename prefix if provided
            if filename_prefix:
                workflow["9"]["inputs"]["filename_prefix"] = filename_prefix
            else:
                # Use recipe name as prefix (sanitized)
                safe_name = "".join(c for c in recipe_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_name = safe_name.replace(' ', '_')[:50]  # Limit length
                workflow["9"]["inputs"]["filename_prefix"] = safe_name
            
            print(f"🎨 Generating image for: {recipe_name}")
            
            # Submit prompt
            result = await self.queue_prompt(workflow)
            prompt_id = result.get('prompt_id')
            
            if not prompt_id:
                print("❌ Failed to get prompt_id from ComfyUI")
                return None
            
            print(f"📋 Prompt queued with ID: {prompt_id}")
            
            # Monitor progress
            success = await self.monitor_progress_websocket(prompt_id)
            
            if not success:
                print("❌ Image generation failed or timed out")
                return None
            
            print("✅ Image generation completed, retrieving...")
            
            # Get the generated image
            history = await self.get_history(prompt_id)
            prompt_history = history.get(prompt_id, {})
            outputs = prompt_history.get('outputs', {})
            
            # Find the saved image
            saved_image_info = None
            for node_id, node_output in outputs.items():
                if 'images' in node_output:
                    images = node_output['images']
                    if images:
                        saved_image_info = images[0]  # Take the first image
                        break
            
            if not saved_image_info:
                print("❌ No image found in generation outputs")
                return None
            
            # Download the image
            image_data = await self.get_image(
                saved_image_info['filename'],
                saved_image_info.get('subfolder', ''),
                saved_image_info.get('type', 'output')
            )
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Save the image with a clean filename
            safe_recipe_name = "".join(c for c in recipe_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_recipe_name = safe_recipe_name.replace(' ', '_')[:50]
            
            # Use original filename extension
            original_filename = saved_image_info['filename']
            file_extension = os.path.splitext(original_filename)[1] or '.png'
            
            output_filename = f"{safe_recipe_name}_{prompt_id[:8]}{file_extension}"
            output_path = os.path.join(output_dir, output_filename)
            
            async with aiofiles.open(output_path, 'wb') as f:
                await f.write(image_data)
            
            print(f"💾 Image saved to: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Error generating image for '{recipe_name}': {str(e)}")
            return None
    
    async def generate_images_for_recipes(
        self, 
        recipes: List[Dict[str, Any]], 
        output_dir: str = "/Users/ben/Code/FoodPal/media"
    ) -> Dict[int, Optional[str]]:
        """
        Generate images for multiple recipes
        
        Args:
            recipes: List of recipe dictionaries
            output_dir: Directory to save images
            
        Returns:
            Dictionary mapping recipe index to image path (or None if failed)
        """
        results = {}
        
        for i, recipe in enumerate(recipes):
            if isinstance(recipe, dict) and 'name' in recipe and 'error' not in recipe:
                recipe_name = recipe['name']
                print(f"🖼️ Generating image {i+1}/{len(recipes)}: {recipe_name}")
                
                image_path = await self.generate_recipe_image(
                    recipe_name, 
                    output_dir,
                    f"recipe_{i+1}"
                )
                results[i] = image_path
                
                # Small delay between generations to avoid overwhelming the server
                await asyncio.sleep(2)
            else:
                print(f"⏭️ Skipping recipe {i+1} (invalid or error)")
                results[i] = None
        
        return results


# Convenience function for easy integration
async def generate_recipe_images(
    recipes: List[Dict[str, Any]], 
    server_address: str = "192.168.4.208:8188",
    output_dir: str = "/Users/ben/Code/FoodPal/media"
) -> Dict[int, Optional[str]]:
    """
    Convenience function to generate images for recipes
    
    Args:
        recipes: List of recipe dictionaries
        server_address: ComfyUI server address
        output_dir: Directory to save images
        
    Returns:
        Dictionary mapping recipe index to image path (or None if failed)
    """
    client = ComfyUIClient(server_address)
    return await client.generate_images_for_recipes(recipes, output_dir)