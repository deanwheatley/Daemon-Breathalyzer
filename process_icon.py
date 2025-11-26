#!/usr/bin/env python3
"""
Process icon to have transparent background.

Converts icon.jpg to icon.png with transparent background.
"""

from PIL import Image
import sys
from pathlib import Path

def remove_background(image_path, output_path=None, threshold=240):
    """
    Remove white/light background from image and save as PNG with transparency.
    
    Args:
        image_path: Path to input image
        output_path: Path to output PNG (if None, replaces input with .png extension)
        threshold: RGB threshold (0-255) for background detection
    """
    try:
        # Load image
        img = Image.open(image_path)
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Get image data
        data = img.getdata()
        
        # Create new image data with transparency
        new_data = []
        for item in data:
            r, g, b, a = item
            # If pixel is very light (white/light background), make it transparent
            if r > threshold and g > threshold and b > threshold:
                # Make transparent
                new_data.append((r, g, b, 0))
            else:
                # Keep original pixel
                new_data.append((r, g, b, a))
        
        # Update image with new data
        img.putdata(new_data)
        
        # Determine output path
        if output_path is None:
            output_path = image_path.with_suffix('.png')
        
        # Save as PNG (supports transparency)
        img.save(output_path, 'PNG')
        print(f"✅ Successfully created {output_path} with transparent background")
        return output_path
        
    except Exception as e:
        print(f"❌ Error processing icon: {e}", file=sys.stderr)
        return None

if __name__ == '__main__':
    # Find icon file
    script_dir = Path(__file__).parent
    icon_jpg = script_dir / 'img' / 'icon.jpg'
    
    if not icon_jpg.exists():
        print(f"❌ Icon file not found: {icon_jpg}", file=sys.stderr)
        sys.exit(1)
    
    # Process icon
    icon_png = script_dir / 'img' / 'icon.png'
    result = remove_background(icon_jpg, icon_png, threshold=220)
    
    if result:
        print(f"✅ Icon processed successfully!")
        print(f"   Input:  {icon_jpg}")
        print(f"   Output: {icon_png}")
        print(f"\n💡 You may want to keep both files for compatibility.")
        sys.exit(0)
    else:
        sys.exit(1)

