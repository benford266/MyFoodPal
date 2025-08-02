"""Utility functions for image handling"""

import base64
import os
from typing import Optional

def image_to_base64(image_path: str) -> Optional[str]:
    """Convert image file to base64 data URL for embedding"""
    try:
        if not os.path.exists(image_path):
            print(f"❌ Image file not found: {image_path}")
            return None
        
        # Get file extension to determine MIME type
        _, ext = os.path.splitext(image_path)
        ext = ext.lower()
        
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        
        mime_type = mime_types.get(ext, 'image/png')
        
        # Read and encode the image
        with open(image_path, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            data_url = f"data:{mime_type};base64,{encoded_string}"
            
        print(f"✅ Converted image to base64: {len(encoded_string)} characters")
        return data_url
        
    except Exception as e:
        print(f"❌ Error converting image to base64: {e}")
        return None

def get_image_display_url(image_path: str, use_base64: bool = False) -> Optional[str]:
    """Get the appropriate URL for displaying an image"""
    if not image_path:
        return None
    
    if use_base64:
        # Convert to absolute path if relative
        if not os.path.isabs(image_path):
            abs_path = os.path.abspath(image_path)
        else:
            abs_path = image_path
        return image_to_base64(abs_path)
    else:
        # Return web-friendly URL
        if image_path.startswith('media/'):
            return f"/{image_path}"
        else:
            # Extract filename and create media URL
            filename = os.path.basename(image_path)
            return f"/media/{filename}"