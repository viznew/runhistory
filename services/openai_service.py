import os
import json
import logging
from typing import Dict, List, Any
from openai import OpenAI
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Enhanced visual style template for images
        self.visual_style = (
            "high-quality historical documentary style, cinematic composition, "
            "dramatic lighting with warm golden hour tones, detailed textures, "
            "photorealistic but with slight painterly quality, rich colors, "
            "atmospheric depth, professional documentary photography aesthetic, "
            "accurate historical details, compelling visual storytelling, "
            "museum-quality artwork style, engaging and educational composition"
        )

    async def generate_script(self, topic: str) -> Dict[str, Any]:
        """Generate script and image prompts for the historical topic"""
        try:
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert historical documentary script writer. "
                            "Generate engaging, factual educational content for video production. "
                            "Create a continuous voiceover script for 60-80 seconds and corresponding "
                            "image prompts that will bring the story to life visually. "
                            "Respond with JSON format containing 'script', 'image_prompts', and 'duration'."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Create a 60-80 second educational video script about: {topic}\n\n"
                            "Requirements:\n"
                            "1. Write an engaging, informative voiceover script\n"
                            "2. Create 12-16 highly detailed image prompts (one per 5 seconds)\n"
                            "3. Each image prompt should be specific, vivid, and historically accurate\n"
                            "4. Include descriptive text overlays for each image with key information\n"
                            "5. Make it educational but entertaining\n"
                            "6. Include estimated duration in seconds\n\n"
                            "Format response as JSON with keys:\n"
                            "- 'script': the voiceover text\n"
                            "- 'image_prompts': array of detailed image descriptions\n"
                            "- 'text_overlays': array of educational text for each image (dates, names, locations, facts)\n"
                            "- 'duration': estimated duration in seconds\n\n"
                            "Example text overlay: 'Ancient Rome, 753 BC' or 'Julius Caesar (100-44 BC)' or 'Battle of Hastings, 1066 AD'"
                        )
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=2000,
                temperature=0.7
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate response structure
            required_keys = ['script', 'image_prompts', 'duration']
            if not all(key in result for key in required_keys):
                raise ValueError("Invalid response format from OpenAI")
            
            # Handle text_overlays - if not provided, create default ones
            if 'text_overlays' not in result:
                result['text_overlays'] = [f"Historical Scene {i+1}" for i in range(len(result['image_prompts']))]
            
            # Ensure text_overlays matches image_prompts length
            if len(result['text_overlays']) != len(result['image_prompts']):
                # Pad or truncate to match
                while len(result['text_overlays']) < len(result['image_prompts']):
                    result['text_overlays'].append("Historical Scene")
                result['text_overlays'] = result['text_overlays'][:len(result['image_prompts'])]
            
            logger.info(f"Generated script with {len(result['image_prompts'])} image prompts")
            return result
            
        except Exception as e:
            logger.error(f"Error generating script: {str(e)}")
            raise Exception(f"Failed to generate script: {str(e)}")

    async def generate_image(self, prompt: str) -> str:
        """Generate image using DALL-E"""
        try:
            # Add visual style to prompt
            full_prompt = f"{prompt}, {self.visual_style}"
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=full_prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            logger.info(f"Generated image for prompt: {prompt[:50]}...")
            
            return image_url
            
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            raise Exception(f"Failed to generate image: {str(e)}")

    async def generate_multiple_images(self, prompts: List[str]) -> List[str]:
        """Generate multiple images with deployment optimizations"""
        try:
            # Process in smaller batches to avoid rate limits and memory issues
            batch_size = 3
            all_urls = []
            
            for i in range(0, len(prompts), batch_size):
                batch = prompts[i:i + batch_size]
                logger.info(f"Processing image batch {i//batch_size + 1}/{(len(prompts) + batch_size - 1)//batch_size}")
                
                # Create tasks for concurrent generation within batch
                tasks = []
                for prompt in batch:
                    task = asyncio.create_task(self.generate_image(prompt))
                    tasks.append(task)
                
                # Wait for batch completion with timeout
                try:
                    batch_urls = await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=120.0  # 2 minute timeout per batch
                    )
                    
                    # Filter out exceptions and return valid URLs
                    for j, result in enumerate(batch_urls):
                        if isinstance(result, Exception):
                            logger.error(f"Failed to generate image {i+j+1}: {str(result)}")
                            continue
                        all_urls.append(result)
                    
                except asyncio.TimeoutError:
                    logger.warning(f"Batch {i//batch_size + 1} timed out, continuing with next batch")
                    continue
                
                # Small delay between batches to avoid rate limits
                if i + batch_size < len(prompts):
                    await asyncio.sleep(1)
            
            logger.info(f"Generated {len(all_urls)} out of {len(prompts)} images")
            return all_urls
            
        except Exception as e:
            logger.error(f"Error generating multiple images: {str(e)}")
            raise Exception(f"Failed to generate images: {str(e)}")
