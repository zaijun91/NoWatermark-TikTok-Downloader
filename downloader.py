import os
import time
import requests
import logging
import re
import asyncio # Import asyncio
# Import the correct fetcher function
from tiktok_fetcher import fetch_tiktok_video_info_rapidapi # Corrected function name
# Define COMMON_HEADERS directly in this file instead of importing
COMMON_HEADERS = {
    'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36 Edg/87.0.664.66'
}

# --- Configuration ---
URL_FILE = "urls.txt"
DOWNLOAD_FOLDER = "downloads"
REQUEST_DELAY_SECONDS = 3 # Delay between requests for info (seconds)
DOWNLOAD_DELAY_SECONDS = 1 # Small delay between downloads (seconds)
MAX_FILENAME_LENGTH = 100 # Limit filename length

# Configure logging (same level as fetcher)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # Reverted level to INFO

# --- Helper Functions ---

def sanitize_filename(name):
    """Removes or replaces characters illegal in Windows filenames."""
    if not name:
        return "untitled"
    # Remove illegal characters: < > : " / \ | ? *
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace whitespace sequences with a single underscore
    name = re.sub(r'\s+', '_', name)
    # Limit length
    return name[:MAX_FILENAME_LENGTH]

def download_file(url, save_path, referer=None, stream=True):
    """Downloads a file from a URL to a specified path."""
    try:
        logging.info(f"  Downloading: {url[:80]}...")
        headers = COMMON_HEADERS.copy() # Start with common headers
        if referer:
            headers['Referer'] = referer

        with requests.get(url, headers=headers, stream=stream, timeout=60) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            if total_size > 0:
                logging.info(f"  File size: {total_size / (1024*1024):.2f} MB")
            else:
                logging.info("  File size: Unknown")

            with open(save_path, 'wb') as f:
                downloaded_size = 0
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    # Optional: Add progress indicator here if needed
            logging.info(f"  Download complete: {os.path.basename(save_path)}")
        return True
    except requests.exceptions.Timeout:
        logging.error(f"  Download timeout for: {url}")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"  Download error for {url}: {e}")
        # Clean up incomplete file
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
                logging.info(f"  Removed incomplete file: {save_path}")
            except OSError as oe:
                logging.error(f"  Error removing incomplete file {save_path}: {oe}")
        return False
    except Exception as e:
        logging.exception(f"  Unexpected download error for {url}: {e}")
        return False

# --- Main Logic ---

async def main(): # Make main async
    print("--- TikTok Batch Downloader (API Method) ---")

    # Check for URL file
    if not os.path.exists(URL_FILE):
        logging.error(f"URL file not found: {URL_FILE}")
        print(f"Error: Please create '{URL_FILE}' and add TikTok URLs (one per line).")
        return

    # Create download directory
    if not os.path.exists(DOWNLOAD_FOLDER):
        logging.info(f"Creating download directory: {DOWNLOAD_FOLDER}")
        os.makedirs(DOWNLOAD_FOLDER)

    # Read URLs
    urls_to_process = []
    with open(URL_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                urls_to_process.append(line)

    if not urls_to_process:
        logging.warning(f"No valid URLs found in {URL_FILE}.")
        return

    logging.info(f"Found {len(urls_to_process)} URLs to process.")

    # Process each URL
    for i, original_url in enumerate(urls_to_process):
        print("-" * 40)
        logging.info(f"Processing URL {i+1}/{len(urls_to_process)}: {original_url}")

        # 1. Fetch video/album info using the correct fetcher (now async)
        info = await fetch_tiktok_video_info_rapidapi(original_url) # Use await with corrected function name

        if not info or info.get('status') != 'success':
            logging.error(f"Failed to fetch info for {original_url}. Reason: {info.get('reason', 'Unknown')}")
            logging.info(f"Waiting {REQUEST_DELAY_SECONDS} seconds before next URL...")
            await asyncio.sleep(REQUEST_DELAY_SECONDS) # Use asyncio.sleep
            continue # Skip to the next URL

        # 2. Handle based on type (Video or Album)
        url_type = info.get('url_type')

        if url_type == 'video':
            video_bytes = info.get('video_bytes')
            video_url = info.get('nwm_video_url') # Fallback URL

            # Check if we have either bytes or a URL
            if not video_bytes and not video_url:
                logging.error(f"No video bytes or URL found for {original_url} despite success status.")
                continue

            author = sanitize_filename(info.get('video_author_nickname', 'unknown_author'))
            # Use the keys returned by the new fetcher function
            video_id = info.get('video_aweme_id', 'unknown_id')
            filename = f"{author}_{video_id}.mp4"
            save_path = os.path.join(DOWNLOAD_FOLDER, filename)

            if os.path.exists(save_path):
                logging.info(f"Video already exists, skipping: {filename}")
            elif video_bytes:
                # Save directly from bytes
                logging.info(f"Attempting to save video from fetched bytes: {filename}")
                try:
                    with open(save_path, 'wb') as f:
                        f.write(video_bytes)
                    logging.info(f"Successfully saved video from bytes: {filename}")
                    download_success = True
                except Exception as e_write:
                    logging.error(f"Error writing video bytes to file {filename}: {e_write}")
                    download_success = False
            elif video_url:
                # Fallback to downloading from URL (might fail with 403)
                logging.warning(f"Attempting to download video from URL (fallback): {filename}")
                # Use the original TikTok page as referer, might help
                referer = f"https://www.tiktok.com/@{info.get('video_author_id', '')}/video/{video_id}"
                download_success = download_file(video_url, save_path, referer=referer)
                if download_success:
                    logging.info(f"Successfully downloaded video from URL: {filename}")
                else:
                    logging.error(f"Failed to download video: {filename}")
                # Small delay after each download attempt
                await asyncio.sleep(DOWNLOAD_DELAY_SECONDS) # Use asyncio.sleep

        elif url_type == 'album':
            image_urls = info.get('album_list')
            if not image_urls:
                logging.error(f"No image list found for album {original_url} despite success status.")
                continue

            # Use the keys returned by the new fetcher function
            author = sanitize_filename(info.get('album_author_nickname', 'unknown_author'))
            album_id = info.get('album_aweme_id', 'unknown_id')
            # Create a subfolder for the album
            album_folder_name = f"{author}_{album_id}"
            album_save_dir = os.path.join(DOWNLOAD_FOLDER, album_folder_name)
            if not os.path.exists(album_save_dir):
                os.makedirs(album_save_dir)
                logging.info(f"Created album directory: {album_folder_name}")

            logging.info(f"Attempting to download {len(image_urls)} images for album: {album_folder_name}")
            # Use the original TikTok page as referer
            # Use the author_id key from the new fetcher's return value
            referer = f"https://www.tiktok.com/@{info.get('album_author_id', '')}/photo/{album_id}"

            for idx, img_url in enumerate(image_urls):
                # Generate filename like 01.jpg, 02.jpg etc.
                # Try to guess extension, default to jpg
                file_ext = os.path.splitext(img_url.split('?')[0])[-1] or ".jpg"
                if len(file_ext) > 5: file_ext = ".jpg" # Basic sanity check
                img_filename = f"{idx+1:02d}{file_ext}"
                img_save_path = os.path.join(album_save_dir, img_filename)

                if os.path.exists(img_save_path):
                    logging.info(f"  Image already exists, skipping: {img_filename}")
                else:
                    download_success = download_file(img_url, img_save_path, referer=referer, stream=False) # Images are usually small
                    if not download_success:
                        logging.error(f"  Failed to download image {idx+1}: {img_filename}")
                    # Small delay after each download attempt
                    await asyncio.sleep(DOWNLOAD_DELAY_SECONDS / 2) # Use asyncio.sleep

            logging.info(f"Finished processing album: {album_folder_name}")

        else:
            logging.warning(f"Unknown URL type '{url_type}' returned for {original_url}")

        # Wait before processing the next URL in the list
        logging.info(f"Waiting {REQUEST_DELAY_SECONDS} seconds before next URL...")
        await asyncio.sleep(REQUEST_DELAY_SECONDS) # Use asyncio.sleep

    print("--- Batch download process finished ---")

if __name__ == "__main__":
    # Ensure required libraries are installed: pip install -r requirements.txt
    asyncio.run(main()) # Run the async main function
