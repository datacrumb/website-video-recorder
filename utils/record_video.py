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
    
    # We want the final video to be 30 seconds, after trimming the first 2 seconds
    trim_seconds = 2
    final_duration = 30
    total_record_duration = trim_seconds + final_duration  # 32 seconds
    scroll_duration = total_record_duration - 1  # 31 seconds for scrolling, 1s at footer
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Create context without recording first
        context = await browser.new_context(**iphone_12)
        page = await context.new_page()
        page.set_default_timeout(60000)
        
        # Try to navigate and extract page content
        try:
            await page.goto(url)
            await page.wait_for_load_state('networkidle')
            await page.wait_for_function('document.readyState === "complete"')
            await asyncio.sleep(2)
            page_text = await page.inner_text('body')
        except Exception as e:
            msg = f"Site not reachable (network error or DNS failure). Skipping video."
            print(f"{msg} ({url}) Exception: {e}")
            return None, msg
        
        # Check for invalid/expired/parked domain or unreachable site phrases
        unreachable_phrases = [
            "This site can’t be reached",
            "server IP address could not be found",
            "DNS_PROBE_FINISHED_NXDOMAIN",
            "Check if there is a typo",
            "Windows Network Diagnostics"
        ]
        invalid_phrases = [
            "domain isn't connected",
            "Looks like this domain isn't",
            "expired domain",
            "Wix.com",
            "This domain is expired",
            "not been registered",
            "is parked",
            "404 Not Found",
            "Site Not Found",
            "No webpage was found"
        ]
        lower_text = page_text.lower()
        if any(phrase.lower() in lower_text for phrase in unreachable_phrases):
            msg = "Site not reachable: This site can’t be reached / DNS_PROBE_FINISHED_NXDOMAIN. Skipping video."
            print(f"{msg} ({url})")
            return None, msg
        if any(phrase.lower() in lower_text for phrase in invalid_phrases):
            msg = "Invalid or expired domain detected. Skipping video."
            print(f"{msg} ({url})")
            return None, msg
        
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
        
        # Start scrolling for most of the video duration
        print("Starting scroll to bottom...")
        await scroll_to_bottom(recording_page, total_duration=scroll_duration)
        print("Scroll completed, waiting at footer if needed...")
        # Wait at the bottom for the rest of the 32 seconds if needed (handled by scroll_to_bottom)
        
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
        
        # Trim the first 2 seconds and keep 30 seconds for the final video
        final_video_path = os.path.join(video_path, f"{website_name}.mp4")
        ffmpeg.input(video_path_mp4, ss=trim_seconds).output(
            final_video_path,
            t=final_duration,
            vcodec='libx264',
            preset='fast',
            crf=23
        ).run(overwrite_output=True)
        
        # Clean up untrimmed video
        if os.path.exists(video_path_mp4):
            os.remove(video_path_mp4)
        
        # Verify final video duration
        final_probe = ffmpeg.probe(final_video_path)
        final_duration_actual = float(final_probe['format']['duration'])
        print(f"Final video duration: {final_duration_actual:.2f} seconds")
        
        return final_video_path, website_name
 