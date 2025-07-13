import os
import asyncio
import logging
from pathlib import Path
from typing import List, Union
from PIL import Image, ImageDraw, ImageFont
import io
import base64

logger = logging.getLogger(__name__)

class ImageOverlayService:
    def __init__(self):
        self.font_size = 48
        self.font_color = (255, 255, 255)  # White
        self.background_color = (0, 0, 0, 180)  # Semi-transparent black
        self.padding = 20
        self.position = 'bottom'  # 'top', 'bottom', 'center'
        
    async def add_text_overlay(
        self,
        image_path: Union[str, Path],
        text: str,
        output_path: Union[str, Path]
    ) -> Path:
        """Add text overlay to an image"""
        try:
            image_path = Path(image_path)
            output_path = Path(output_path)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Open the image
            with Image.open(image_path) as img:
                # Convert to RGBA if not already
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Create a drawing context
                draw = ImageDraw.Draw(img)
                
                # Try to load a font, fallback to default if not available
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", self.font_size)
                except (OSError, IOError):
                    try:
                        font = ImageFont.truetype("arial.ttf", self.font_size)
                    except (OSError, IOError):
                        font = ImageFont.load_default()
                
                # Get text dimensions
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                # Calculate position
                img_width, img_height = img.size
                
                if self.position == 'bottom':
                    x = (img_width - text_width) // 2
                    y = img_height - text_height - self.padding * 2
                elif self.position == 'top':
                    x = (img_width - text_width) // 2
                    y = self.padding
                else:  # center
                    x = (img_width - text_width) // 2
                    y = (img_height - text_height) // 2
                
                # Create background rectangle
                bg_x1 = x - self.padding
                bg_y1 = y - self.padding
                bg_x2 = x + text_width + self.padding
                bg_y2 = y + text_height + self.padding
                
                # Create overlay for background
                overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                
                # Draw background rectangle
                overlay_draw.rectangle(
                    [bg_x1, bg_y1, bg_x2, bg_y2],
                    fill=self.background_color
                )
                
                # Composite the overlay
                img = Image.alpha_composite(img, overlay)
                
                # Draw text
                draw = ImageDraw.Draw(img)
                draw.text((x, y), text, font=font, fill=self.font_color)
                
                # Convert back to RGB for saving
                if img.mode == 'RGBA':
                    # Create a white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                    img = background
                
                # Save the result
                img.save(output_path, 'PNG', quality=95)
                
            logger.info(f"Added text overlay '{text}' to image: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding text overlay: {str(e)}")
            # If overlay fails, just copy the original image
            import shutil
            shutil.copy2(image_path, output_path)
            return output_path
    
    async def add_multiple_overlays(
        self,
        image_paths: List[Path],
        texts: List[str],
        output_dir: Path
    ) -> List[Path]:
        """Add text overlays to multiple images"""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Ensure we have matching numbers of images and texts
            min_count = min(len(image_paths), len(texts))
            
            tasks = []
            output_paths = []
            
            for i in range(min_count):
                input_path = image_paths[i]
                text = texts[i]
                output_path = output_dir / f"overlay_{input_path.name}"
                output_paths.append(output_path)
                
                task = self.add_text_overlay(input_path, text, output_path)
                tasks.append(task)
            
            # Process all overlays concurrently
            await asyncio.gather(*tasks)
            
            logger.info(f"Added text overlays to {len(output_paths)} images")
            return output_paths
            
        except Exception as e:
            logger.error(f"Error adding multiple overlays: {str(e)}")
            # Return original paths if overlay fails
            return image_paths[:min_count]
    
    def set_style(
        self,
        font_size: int = None,
        font_color: tuple = None,
        background_color: tuple = None,
        position: str = None,
        padding: int = None
    ):
        """Customize the overlay style"""
        if font_size is not None:
            self.font_size = font_size
        if font_color is not None:
            self.font_color = font_color
        if background_color is not None:
            self.background_color = background_color
        if position is not None:
            self.position = position
        if padding is not None:
            self.padding = padding