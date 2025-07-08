from playwright.async_api import async_playwright
from .extract_name import extract_website_name
from .scroll import scroll_to_bottom
import asyncio
import sys
import os
import ffmpeg

async def record_website(url: str, video_path: str = "videos"):
    website_name = extract_website_name(url)
    # Emulate a mobile device (e.g., iPhone 12)
    iphone_12 = {
        "viewport": {"width": 390, "height": 844},
        "device_scale_factor": 3,
        "is_mobile": True,
        "has_touch": True,
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    }
    os.makedirs(video_path, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Create context without recording first
        context = await browser.new_context(**iphone_12)
        page = await context.new_page()
        page.set_default_timeout(60000)
        
        # Navigate to the page
        await page.goto(url)
        
        # Wait for the page to be fully loaded
        await page.wait_for_load_state('networkidle')
        
        # Additional wait to ensure DOM is fully rendered
        await page.wait_for_function('document.readyState === "complete"')
        
        # Wait a bit more for any dynamic content to load
        await asyncio.sleep(2)
        
        # Now start recording by creating a new context with recording
        await context.close()
        recording_context = await browser.new_context(
            **iphone_12,
            record_video_dir=video_path,
            record_video_size={"width": 390, "height": 844}
        )
        recording_page = await recording_context.new_page()
        recording_page.set_default_timeout(60000)
        
        # Navigate to the same page in the recording context
        await recording_page.goto(url, wait_until='domcontentloaded')
        await recording_page.wait_for_function('document.readyState === "complete"')
        await asyncio.sleep(4)
        
        # Now scroll to record the content
        await scroll_to_bottom(recording_page)
        await asyncio.sleep(1)
        
        video_path_webm = await recording_page.video.path()
        await recording_context.close()
        
        # Check file exists and is not empty
        if not os.path.exists(video_path_webm) or os.path.getsize(video_path_webm) == 0:
            print(f"Video file {video_path_webm} does not exist or is empty.")
            return None, website_name
            
        # Convert .webm to .mp4 with website name
        video_path_mp4 = os.path.join(video_path, f"{website_name}_untrimmed.mp4")
        ffmpeg.input(video_path_webm).output(
            video_path_mp4,
            vcodec='libx264',
            preset='fast',
            crf=23
        ).run(overwrite_output=True)
        print(f"Converted video saved to: {video_path_mp4}")
        
        # Delete original .webm file after converting
        if os.path.exists(video_path_webm):
            os.remove(video_path_webm)
            print(f"Deleted original .webm file: {video_path_webm}")
        
        # Trim first 4 seconds from .mp4 and save as website_name_trimmed.mp4
        trimmed_video_path = os.path.join(video_path, f"{website_name}.mp4")
        ffmpeg.input(video_path_mp4, ss=7).output(
            trimmed_video_path,
            c='copy'  # no re-encoding, fast
        ).run(overwrite_output=True)
        
        # delete original mp4 if not needed
        if os.path.exists(video_path_mp4):
            os.remove(video_path_mp4)
        
        return trimmed_video_path, website_name
 