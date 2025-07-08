from playwright.async_api import async_playwright
import asyncio
import sys
import os
from sheets import Sheets
from drive import upload_file_to_drive
import ffmpeg

async def scroll_to_bottom(page, step=200, delay=0.1, max_attempts=50):
    attempts = 0
    while attempts < max_attempts:
        reached_bottom = await page.evaluate('''(step) => {
            const { scrollTop, scrollHeight, clientHeight } = document.scrollingElement || document.documentElement;
            if (scrollTop + clientHeight >= scrollHeight - 1) return true;
            window.scrollBy({ top: step, behavior: 'smooth' });
            return false;
        }''', step)
        if reached_bottom:
            break
        attempts += 1
        await asyncio.sleep(delay)
    # If the page is very short, just wait a bit
    if attempts == 0:
        await asyncio.sleep(2)

async def record_website(url: str, video_path: str = "videos"):
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
        await recording_page.goto(url)
        
        # Wait for the page to be fully loaded again
        await recording_page.wait_for_load_state('networkidle')
        await recording_page.wait_for_function('document.readyState === "complete"')
        await asyncio.sleep(2)
        
        # Now scroll to record the content
        await scroll_to_bottom(recording_page)
        await asyncio.sleep(1)
        
        video_path_webm = await recording_page.video.path()
        await recording_context.close()
        
        # Check file exists and is not empty
        if not os.path.exists(video_path_webm) or os.path.getsize(video_path_webm) == 0:
            print(f"Video file {video_path_webm} does not exist or is empty.")
            return None
            
        # Convert .webm to .mp4
        video_path_mp4 = video_path_webm.replace(".webm", ".mp4")
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

        return video_path_mp4
 
async def main():
    sheets = Sheets()
    urls = sheets.get_existing_urls()
    drive_folder_id = "1k9PNkTVxwnpTgvnhp4IAU8jPF9M3IeeR"
    for idx, url in enumerate(urls, start=2):  # start=2 if row 1 is header
        if not url.strip():
            print(f"Skipping empty URL at row {idx}")
            continue
        print(f"Processing row {idx}: {url}")
        video_path = await record_website(url)
        if video_path: # Only upload if video was recorded
            drive_url = upload_file_to_drive(video_path, folder_id=drive_folder_id)
            sheets.update_video_link(idx, drive_url)
            print(f"Appended video link to sheet: {drive_url}")
        else:
            print(f"Skipped video recording for row {idx}: {url}")

if __name__ == "__main__":
    asyncio.run(main())
        
