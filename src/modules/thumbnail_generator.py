from PIL import Image, ImageDraw, ImageFont
from src.config import THUMBNAILS_DIR, DEFAULT_FONT_NAME
import os

class ThumbnailGenerator:
    def __init__(self):
        THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
        
    def generate(self, video_path: str, title: str, subtitle: str, output_filename: str):
        # MVP: Create a simple black background thumbnail with text
        # In a real app, we might extract the first frame from the video
        img = Image.new('RGB', (1080, 1920), color='black')
        draw = ImageDraw.Draw(img)
        
        try:
            font_title = ImageFont.truetype("arial.ttf", 80)
            font_subtitle = ImageFont.truetype("arial.ttf", 50)
        except IOError:
            font_title = ImageFont.load_default()
            font_subtitle = ImageFont.load_default()
            
        draw.text((540, 800), title, font=font_title, fill="white", anchor="mm")
        draw.text((540, 1000), subtitle, font=font_subtitle, fill="gray", anchor="mm")
        
        output_path = THUMBNAILS_DIR / output_filename
        img.save(output_path)
        
        return str(output_path)
