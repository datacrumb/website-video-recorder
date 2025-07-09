from drive import upload_file_to_drive
from utils import record_website
from sheets import Sheets
import asyncio
import ffmpeg

async def main():
    sheets = Sheets()
    rows = sheets.get_existing_rows()
    drive_folder_id = "1k9PNkTVxwnpTgvnhp4IAU8jPF9M3IeeR"
    for idx, row in enumerate(rows[1:], start=2):  # start=2 if row 1 is header
        url = row[0] if len(row) > 0 else ''
        video_link = row[2] if len(row) > 2 else ''
        if not url.strip():
            print(f"Skipping empty URL at row {idx}")
            continue
        if video_link.strip():
            print(f"Skipping row {idx} (video link already present)")
            continue
        print(f"Processing row {idx}: {url}")
        try:
            video_path, website_name = await record_website(url)
            if video_path: # Only upload if video was recorded
                drive_url = upload_file_to_drive(video_path, folder_id=drive_folder_id)
                # Update: website name in col 2, link in col 3
                sheets.update_website_info(idx, website_name, drive_url)
                print(f"Appended website name and video link to sheet: {website_name}, {drive_url}")
            else:
                print(f"Skipped video recording for row {idx}: {url}")
        except Exception as e:
            print(f"Error processing row {idx} ({url}): {e}")
            continue

if __name__ == "__main__":
    asyncio.run(main())
        
