import sys
import os
import logging
import asyncio
import time
import re # Import re for sanitize_filename
import json # Import json for config
# import requests # Keep commented out for now, import locally if needed (e.g., proxy test)
import functools # Import functools for partial
from datetime import datetime # Import datetime for template variables
import aiohttp # Import aiohttp for async requests
import aiofiles # Import aiofiles for async file writing
import aiofiles.os # Import aiofiles.os for async file operations
# --- I18N Imports ---
from PySide6.QtCore import QTranslator, QLocale, QLibraryInfo
# --------------------
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QFileDialog, QMessageBox, QHeaderView,
    QStyle, QProgressBar, QSpinBox, QFormLayout, QCheckBox,
    QGroupBox, QRadioButton, QGridLayout, QMainWindow,
    QStackedWidget, QDialog, QDialogButtonBox, # Removed QListWidget, QListWidgetItem, Added QDialogButtonBox
    QComboBox # Import QComboBox
    # QTabWidget no longer needed
)
import random # Import random for test_proxy headers
from PySide6.QtGui import QIcon, QColor, QLinearGradient, QPalette, QAction, QPixmap # Import QAction, QPixmap
from PySide6.QtCore import Qt, QThread, Signal, Slot, QRunnable, QThreadPool, QObject, QSize # Import QObject, QSize

# Import necessary functions from our other modules
# --- Updated Import: Use the new main fetcher function ---
from tiktok_fetcher import fetch_tiktok_info
# -------------------------------------------------------
# Define COMMON_HEADERS directly or import if moved to a config file
COMMON_HEADERS = {
    'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36 Edg/87.0.664.66'
}
MAX_FILENAME_LENGTH = 100 # From downloader.py config
REQUEST_DELAY_SECONDS = 1 # Reduced delay for concurrency testing
DOWNLOAD_DELAY_SECONDS = 0.5 # Reduced delay for concurrency testing
PROGRESS_UPDATE_INTERVAL = 0.5 # Update progress display every 0.5 seconds
DEFAULT_CONCURRENCY = 3 # Default number of concurrent downloads
CONFIG_FILE = "config.json" # Define config file name
DEFAULT_THEME = "light" # Default theme

# --- QSS Themes (Moved to Module Level) ---
LIGHT_THEME_QSS = """
    QMainWindow, QWidget {
        background-color: #f0f0f0; /* Light grey background */
        color: #333333; /* Dark text */
        font-family: "Helvetica Neue", "Segoe UI", Arial, sans-serif; /* Modern font stack */
    }
    QGroupBox {
        background-color: #ffffff; /* White background for group boxes */
        border: 1px solid #cccccc;
        border-radius: 8px; /* Slightly more rounded */
        margin-top: 12px; /* Space for title */
        padding: 12px; /* More padding */
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        left: 10px;
        color: #333333; /* Dark title text */
        font-weight: bold;
    }
    QLabel {
        color: #333333; /* Dark text */
        background-color: transparent;
    }
    QLineEdit, QTextEdit, QSpinBox, QCheckBox, QComboBox { /* Added QComboBox */
        background-color: #ffffff; /* White background for inputs */
        border: 1px solid #cccccc;
        border-radius: 4px;
        padding: 6px; /* More padding */
        color: #333333; /* Dark text */
    }
    QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
        border: 1px solid #007aff; /* Blue focus border */
        background-color: #ffffff;
    }
    QComboBox::drop-down {
        border: none;
    }
    QComboBox::down-arrow {
        /* Consider using a dark-colored SVG for light mode */
        image: url(img/down.svg); /* Example: Needs a standard down arrow */
        width: 12px;
        height: 12px;
        margin-right: 5px;
    }
    QPushButton {
        background-color: #e0e0e0; /* Light grey button */
        border: 1px solid #cccccc;
        border-radius: 4px;
        padding: 6px 18px; /* More padding */
        color: #333333; /* Dark text */
        min-height: 22px; /* Slightly taller */
    }
    QPushButton:hover {
        background-color: #d0d0d0; /* Slightly darker on hover */
        border-color: #bbbbbb;
    }
    QPushButton:pressed {
        background-color: #c0c0c0; /* Even darker when pressed */
        border-color: #aaaaaa;
    }
    QPushButton:disabled {
        background-color: #f5f5f5; /* Very light grey */
        color: #aaaaaa; /* Dimmed text */
        border-color: #dddddd;
    }
    QTableWidget {
        background-color: #ffffff; /* White background */
        border: 1px solid #cccccc;
        gridline-color: #e0e0e0; /* Light grid lines */
        alternate-background-color: #f9f9f9; /* Very subtle alternating row color */
        selection-background-color: #007aff; /* Blue selection */
        selection-color: #ffffff; /* White text on selection */
        color: #333333; /* Dark text for table content */
    }
    QHeaderView::section {
        background-color: #f0f0f0; /* Header background */
        border: none;
        border-bottom: 1px solid #cccccc;
        padding: 4px;
        font-weight: bold;
        color: #333333; /* Dark header text */
    }
    QProgressBar {
        border: 1px solid #cccccc;
        border-radius: 4px;
        text-align: center;
        background-color: #e0e0e0; /* Light grey background */
        height: 18px;
        color: #333333; /* Dark text on progress bar */
    }
    QProgressBar::chunk {
        background-color: #4CAF50; /* Green chunk */
        border-radius: 3px;
        margin: 1px;
    }
    QRadioButton::indicator {
        width: 13px;
        height: 13px;
    }
    QListWidget {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 4px;
        color: #333333; /* Dark text for list items */
    }
    QListWidget::item:selected {
        background-color: #007aff; /* Blue selection */
        color: #ffffff; /* White text on selection */
    }
    QMenuBar {
        background-color: #f0f0f0;
        color: #333333;
    }
    QMenuBar::item:selected {
        background-color: #e0e0e0;
    }
    QMenu {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        color: #333333;
    }
    QMenu::item:selected {
        background-color: #007aff;
        color: #ffffff;
    }
    QToolTip {
        background-color: #ffffdd; /* Light yellow tooltip */
        color: #333333; /* Dark text */
        border: 1px solid #cccccc;
        padding: 2px;
    }
"""

DARK_THEME_QSS = """
    QMainWindow, QWidget {
        background-color: #2b2b2b; /* Dark grey background */
        color: #f0f0f0; /* Light text */
        font-family: "Helvetica Neue", "Segoe UI", Arial, sans-serif; /* Prioritize Helvetica Neue */
    }
    QGroupBox {
        background-color: #3c3c3c; /* Slightly lighter dark grey */
        border: 1px solid #555555;
        border-radius: 8px;
        margin-top: 12px; /* Slightly more space for title */
        padding: 12px; /* Increased padding */
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        left: 10px;
        color: #f0f0f0; /* Light title text */
        font-weight: bold;
    }
    QLabel {
        color: #f0f0f0; /* Light text */
        background-color: transparent;
    }
    QLineEdit, QTextEdit, QSpinBox, QCheckBox, QComboBox { /* Added QComboBox */
        background-color: #3c3c3c; /* Dark background for inputs */
        border: 1px solid #555555;
        border-radius: 4px;
        padding: 6px; /* Increased padding */
        color: #f0f0f0; /* Light text */
    }
    QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
        border: 1px solid #007aff; /* Keep blue focus border */
        background-color: #4a4a4a; /* Slightly lighter on focus */
    }
    QComboBox::drop-down {
        border: none;
    }
    QComboBox::down-arrow {
        /* Use the existing dark arrow for now to avoid errors */
        image: url(img/down.svg); /* Changed from down-light.svg */
        width: 12px;
        height: 12px;
        margin-right: 5px;
    }
    QPushButton {
        background-color: #555555; /* Medium grey button */
        border: 1px solid #666666;
        border-radius: 4px;
        padding: 6px 18px; /* Increased padding */
        color: #f0f0f0; /* Light text */
        min-height: 22px; /* Slightly taller */
    }
    QPushButton:hover {
        background-color: #666666; /* Lighter grey on hover */
        border-color: #777777;
    }
    QPushButton:pressed {
        background-color: #444444; /* Darker grey when pressed */
        border-color: #555555;
    }
    QPushButton:disabled {
        background-color: #404040;
        color: #888888; /* Dimmed text */
        border-color: #505050;
    }
    QTableWidget {
        background-color: #3c3c3c; /* Dark background */
        border: 1px solid #555555;
        gridline-color: #555555; /* Darker grid lines */
        alternate-background-color: #424242; /* Subtle alternating row color */
        selection-background-color: #007aff; /* Blue selection */
        selection-color: #ffffff; /* White text on selection */
        color: #f0f0f0; /* Light text for table content */
    }
    QHeaderView::section {
        background-color: #4a4a4a; /* Header background */
        border: none;
        border-bottom: 1px solid #555555;
        padding: 4px;
        font-weight: bold;
        color: #f0f0f0; /* Light header text */
    }
    QProgressBar {
        border: 1px solid #555555;
        border-radius: 4px;
        text-align: center;
        background-color: #4a4a4a; /* Dark background */
        height: 18px;
        color: #f0f0f0; /* Light text on progress bar */
    }
    QProgressBar::chunk {
        background-color: #007aff; /* Keep blue chunk */
        border-radius: 3px;
        margin: 1px;
    }
    QRadioButton::indicator {
        width: 13px;
        height: 13px;
        /* Add specific styling for dark mode if needed */
    }
    QCheckBox::indicator {
         /* Add specific styling for dark mode if needed */
    }
    QListWidget {
        background-color: #3c3c3c;
        border: 1px solid #555555;
        border-radius: 4px;
        color: #f0f0f0; /* Light text for list items */
    }
    QListWidget::item:selected {
        background-color: #007aff; /* Blue selection */
        color: #ffffff; /* White text on selection */
    }
    QMenuBar {
        background-color: #3c3c3c;
        color: #f0f0f0;
    }
    QMenuBar::item:selected {
        background-color: #555555;
    }
    QMenu {
        background-color: #3c3c3c;
        border: 1px solid #555555;
        color: #f0f0f0;
    }
    QMenu::item:selected {
        background-color: #007aff;
        color: #ffffff;
    }
    QToolTip {
        background-color: #4a4a4a; /* Dark tooltip */
        color: #f0f0f0; /* Light text */
        border: 1px solid #555555;
        padding: 2px;
    }
"""
# ---------------------------------------

# Configure logging (can be refined later)
# Ensure logging works well with GUI and threads
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s') # Added funcName
log_handler = logging.StreamHandler(sys.stdout) # Log to console for now
log_handler.setFormatter(log_formatter)
logger = logging.getLogger()
# Prevent adding handler multiple times if script is re-run in some contexts
if not logger.handlers:
    logger.addHandler(log_handler)
logger.setLevel(logging.INFO) # Set level to INFO


# --- Helper Functions ---

# --- Helper Functions ---

# get_base_path is no longer needed for config, but might be useful for other resources
# def get_base_path(): ... (Keep or remove if unused elsewhere)

def get_user_config_path(): # Renamed for clarity
    """
    Returns the absolute path to the config file in the user's Roaming AppData directory.
    Example: C:\\Users\\<username>\\AppData\\Roaming\\TikBolt\\config.json
    """
    app_name = "TikBolt" # Define the application name for the folder
    try:
        # Get the Roaming AppData path (most common place for user config on Windows)
        appdata_path = os.getenv('APPDATA')
        if not appdata_path: # Fallback if APPDATA is not set (unlikely on Windows)
            appdata_path = os.path.expanduser("~")
            logger.warning("APPDATA 环境变量未设置，将尝试使用用户主目录。")

        config_dir = os.path.join(appdata_path, app_name)
        return os.path.join(config_dir, CONFIG_FILE)
    except Exception as e:
        # Critical fallback: Use current working directory if AppData fails entirely
        logger.exception(f"获取用户 AppData 路径时发生严重错误: {e}. 将回退到当前工作目录。")
        # Use a different fallback filename to avoid conflict? Or just log clearly.
        return os.path.join(os.getcwd(), f"user_{CONFIG_FILE}") # Fallback to CWD with prefix

def get_bundled_config_path():
    """
    Returns the path to the config file bundled with the application
    (expected to be next to the executable or script).
    """
    if getattr(sys, 'frozen', False):
        # Running as bundled executable (e.g., PyInstaller)
        # sys.executable is the path to the exe
        app_path = os.path.dirname(sys.executable)
    else:
        # Running as a script
        # __file__ is the path to the current script
        app_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(app_path, CONFIG_FILE)

def sanitize_filename(name):
    """Removes or replaces characters illegal in Windows filenames."""
    if not name:
        return "untitled"
    # Remove illegal characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace whitespace with underscores
    name = re.sub(r'\s+', '_', name)
    # Limit length
    return name[:MAX_FILENAME_LENGTH]


# --- NEW Async Download Function ---
async def download_file_async(url, save_path, referer=None, progress_callback=None, row_index=-1, proxies=None, session=None):
    """
    Asynchronous version of download_file using aiohttp and aiofiles.
    Includes progress reporting via callback, passing row_index, and proxy support.
    Accepts an optional aiohttp.ClientSession.
    """
    close_session = False
    if session is None:
        # Create a connector that respects proxy settings if provided
        # Note: aiohttp uses proxy URL string directly, not dict like requests
        proxy_url = None
        if proxies:
            # Assuming proxies dict has 'http' or 'https' key with the full proxy URL
            proxy_url = proxies.get('https') or proxies.get('http')

        # Use TrustEnvironment=True to potentially pick up system proxies if proxy_url is None
        # Explicitly disable SSL verification if needed (not recommended generally)
        # connector = aiohttp.TCPConnector(ssl=False) if disable_ssl else aiohttp.TCPConnector()
        connector = aiohttp.TCPConnector() # Default connector
        session = aiohttp.ClientSession(connector=connector, headers=COMMON_HEADERS)
        close_session = True
        logger.debug(f"  [Row {row_index}] Created new aiohttp session. Proxy URL: {proxy_url}")

    try:
        headers = {} # Start fresh, session might have base headers
        if referer:
            headers['Referer'] = referer

        # Use proxy_url in the get request if specified
        proxy_arg = proxy_url if proxies else None # Use the extracted proxy URL string

        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=60), proxy=proxy_arg) as response:
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            last_update_time = time.time()
            start_time = last_update_time

            async with aiofiles.open(save_path, 'wb') as f:
                async for chunk in response.content.iter_chunked(8192):
                    if chunk:
                        await f.write(chunk)
                        downloaded_size += len(chunk)
                        current_time = time.time()
                        elapsed_time_total = current_time - start_time
                        elapsed_time_update = current_time - last_update_time

                        # --- Progress and Speed Calculation ---
                        if progress_callback and elapsed_time_update >= PROGRESS_UPDATE_INTERVAL:
                            progress_percent = int(100 * downloaded_size / total_size) if total_size > 0 else 0
                            speed_bps = downloaded_size / elapsed_time_total if elapsed_time_total > 0 else 0
                            speed_mbps = speed_bps / 1024 / 1024
                            # Call the callback (ensure it's thread-safe if needed, but here it's called from the same async loop)
                            progress_callback(row_index, downloaded_size, total_size, progress_percent, speed_mbps)
                            last_update_time = current_time
                        # ------------------------------------
                    # Yield control briefly to allow other tasks to run
                    await asyncio.sleep(0.001)


            logger.info(f"  [Row {row_index}] Async download complete: {os.path.basename(save_path)}")
            # --- File Size Validation (Basic) ---
            # Use aiofiles for async stat
            stat_result = await aiofiles.os.stat(save_path)
            actual_size = stat_result.st_size
            if total_size > 0 and actual_size != total_size:
                size_mismatch_msg = f"文件大小不匹配. 预期: {total_size}, 实际: {actual_size}"
                logger.warning(f"  [Row {row_index}] {size_mismatch_msg} for {save_path}")
                return True, size_mismatch_msg # Return success=True but with a warning message
            # ------------------------------------
        return True, None # Return success, no error message

    # --- Improved Error Handling ---
    except aiohttp.ClientProxyConnectionError as e:
        error_msg = f"代理连接错误: {e}" # More user-friendly
        logger.error(f"  [Row {row_index}] Proxy connection error for {url}: {e}")
        return False, error_msg
    except asyncio.TimeoutError:
        error_msg = "下载超时" # More user-friendly
        logger.error(f"  [Row {row_index}] Download timeout for {url}")
        return False, error_msg
    except aiohttp.ClientResponseError as e: # Specific HTTP errors
        error_msg = f"HTTP 错误 {e.status}: {e.message}" # More user-friendly
        logger.error(f"  [Row {row_index}] HTTP error {e.status} for {url}: {e.message}")
        return False, error_msg
    except aiohttp.ClientConnectionError as e: # Specific connection errors
        error_msg = f"网络连接错误: {e}" # More user-friendly
        logger.error(f"  [Row {row_index}] Connection error for {url}: {e}")
        return False, error_msg
    except aiohttp.ClientError as e: # Catch other aiohttp client errors
        error_msg = f"下载客户端错误: {e}" # More user-friendly
        logger.error(f"  [Row {row_index}] Client error for {url}: {e}")
        # Attempt to remove incomplete file asynchronously
        if await aiofiles.os.path.exists(save_path):
            try:
                await aiofiles.os.remove(save_path)
                logger.info(f"  [Row {row_index}] 已移除不完整文件: {save_path}")
            except OSError as oe:
                 logger.error(f"  [Row {row_index}] 移除不完整文件错误 {save_path}: {oe}")
        return False, error_msg
    except Exception as e:
        error_msg = f"发生意外错误: {e}" # More user-friendly
        logger.exception(f"  [Row {row_index}] Unexpected error downloading {url}: {e}")
        return False, error_msg
    # -----------------------------
    finally:
        if close_session and session:
            await session.close()
            logger.debug(f"  [Row {row_index}] Closed internally created aiohttp session.")


# --- Synchronous Download Function (Keep for Cover/Title for simplicity?) ---
# Modify download_file_sync to accept and use proxies
def download_file_sync(url, save_path, referer=None, stream=True, progress_callback=None, row_index=-1, proxies=None): # Add proxies
    """
    Synchronous version of download_file for the worker thread.
    Includes progress reporting via callback, passing row_index, and proxy support.
    NOW USED PRIMARILY FOR COVERS or potentially proxy testing.
    Includes progress reporting via callback, passing row_index, and proxy support.
    """
    try:
        # logger.info(f"  [Row {row_index}] Downloading: {url[:80]}...") # Optional: Add row index to log
        headers = COMMON_HEADERS.copy()
        if referer:
            headers['Referer'] = referer

        # Use proxies if provided
        # --- Import requests locally for sync download ---
        import requests
        # -----------------------------------------------
        with requests.get(url, headers=headers, stream=stream, timeout=60, proxies=proxies) as r: # Pass proxies
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded_size = 0
            last_update_time = time.time()
            start_time = last_update_time

            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        current_time = time.time()
                        elapsed_time_total = current_time - start_time
                        elapsed_time_update = current_time - last_update_time

                        # --- Progress and Speed Calculation ---
                        if progress_callback and elapsed_time_update >= PROGRESS_UPDATE_INTERVAL:
                            progress_percent = int(100 * downloaded_size / total_size) if total_size > 0 else 0
                            speed_bps = downloaded_size / elapsed_time_total if elapsed_time_total > 0 else 0
                            speed_mbps = speed_bps / 1024 / 1024
                            # Pass row_index to the callback
                            progress_callback(row_index, downloaded_size, total_size, progress_percent, speed_mbps)
                            last_update_time = current_time
                        # ------------------------------------

            logger.info(f"  [Row {row_index}] Download complete: {os.path.basename(save_path)}")
            # --- File Size Validation (Basic) ---
            actual_size = os.path.getsize(save_path)
            if total_size > 0 and actual_size != total_size:
                size_mismatch_msg = f"文件大小不匹配. 预期: {total_size}, 实际: {actual_size}"
                logger.warning(f"  [Row {row_index}] {size_mismatch_msg} for {save_path}")
                return True, size_mismatch_msg
            # ------------------------------------
        return True, None # Return success, no error message
    except requests.exceptions.ProxyError as e: # Specific proxy error handling
        error_msg = f"代理错误 {url}: {e}"
        logger.error(f"  [Row {row_index}] {error_msg}")
        return False, error_msg
    except requests.exceptions.Timeout:
        error_msg = f"下载超时: {url}"
        logger.error(f"  [Row {row_index}] {error_msg}")
        return False, error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"下载错误 {url}: {e}"
        logger.error(f"  [Row {row_index}] {error_msg}")
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
                logger.info(f"  [Row {row_index}] 已移除不完整文件: {save_path}")
            except OSError as oe:
                logger.error(f"  [Row {row_index}] 移除不完整文件错误 {save_path}: {oe}")
        return False, error_msg
    except Exception as e:
        error_msg = f"未预期的下载错误 {url}: {e}"
        logger.exception(f"  [Row {row_index}] {error_msg}")
        return False, error_msg


# --- Configuration Loading/Saving ---
def load_config():
    """
    Loads configuration using the following priority:
    1. User-specific config from AppData (%APPDATA%/TikBolt/config.json)
    2. Bundled config next to the executable/script (config.json)
    3. Hardcoded default config if neither is found or loadable.
    """
    user_config_path = get_user_config_path() # Path in AppData
    bundled_config_path = get_bundled_config_path() # Path next to EXE/script
    config_to_load = None
    loaded_from = None

    # Updated default config structure
    default_config = {
        "api_endpoints": [], # Now a list of dictionaries
        "active_api_name": None, # Store the name of the active API
        "download_path": "",
        "download_cover_title": False,
        "cover_title_path": "",
        "theme": DEFAULT_THEME,
        "preferred_language": None,
        "proxy_config": { # Added proxy config section
            "type": "none", # 'none', 'system', 'http', 'socks5'
            "address": "",
            "port": "",
            "username": "",
            "password": ""
        }
    }

    logger.info(f"[Config] 尝试从用户路径加载: {user_config_path}")
    if os.path.exists(user_config_path):
        config_to_load = user_config_path
        loaded_from = "user"
    else:
        logger.info(f"[Config] 用户配置文件未找到。尝试从捆绑路径加载: {bundled_config_path}")
        if os.path.exists(bundled_config_path):
            config_to_load = bundled_config_path
            loaded_from = "bundled"
        else:
            logger.warning(f"[Config] 用户配置和捆绑配置均未找到。将使用硬编码的默认设置。")
            # Return default config directly if neither exists
            return default_config.copy() # Make sure to return a copy

    # Proceed to load from config_to_load path
    logger.info(f"[Config] 正在加载配置文件: {config_to_load} (来源: {loaded_from})")
    try:
        with open(config_to_load, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"[Config] 成功加载配置文件: {config_to_load}")
        # --- DEBUG: Log loaded config content ---
        # logger.debug(f"[Config] Raw loaded config: {config}")
        # ---------------------------------------
        # Ensure essential keys exist, merging with defaults (Corrected Indentation)
        final_config = default_config.copy() # Start with defaults
        final_config.update(config) # Update with loaded values

        # Validate api_endpoints structure (Corrected Indentation)
        validated_endpoints = []
        if isinstance(final_config.get("api_endpoints"), list):
            for ep in final_config["api_endpoints"]:
                # Corrected if/else block structure and indentation
                if isinstance(ep, dict) and 'name' in ep and 'url' in ep:
                    # Ensure required fields exist, add defaults for optional ones
                    ep.setdefault('key', '')
                    ep.setdefault('host', '')
                    ep.setdefault('param_name', 'url')
                    ep.setdefault('method', 'GET')
                    validated_endpoints.append(ep)
                else:
                    logger.warning(f"配置文件中发现无效的 API 端点条目，已忽略: {ep}")
        final_config["api_endpoints"] = validated_endpoints

        # Ensure active_api_name is valid or None (Corrected Indentation)
        active_name = final_config.get("active_api_name")
        if active_name and not any(ep['name'] == active_name for ep in final_config["api_endpoints"]):
            logger.warning(f"配置文件中的活动 API 名称 '{active_name}' 无效或不存在，已重置为 null。")
            final_config["active_api_name"] = None

        # Validate proxy_config structure (ensure it's a dict and has required keys) (Corrected Indentation)
        if not isinstance(final_config.get("proxy_config"), dict):
            logger.warning("配置文件中的 proxy_config 无效 (非字典)，已重置为默认值。")
            final_config["proxy_config"] = default_config["proxy_config"].copy()
        else:
            # Ensure all keys from default exist
            final_config["proxy_config"] = {**default_config["proxy_config"], **final_config["proxy_config"]}
            # Validate proxy type
            valid_proxy_types = ['none', 'system', 'http', 'socks5']
            if final_config["proxy_config"].get("type") not in valid_proxy_types:
                logger.warning(f"配置文件中的代理类型 '{final_config['proxy_config'].get('type')}' 无效，已重置为 'none'。")
            final_config["proxy_config"]["type"] = "none"

        # --- Add Default APIs if list is empty ---
        if not final_config.get("api_endpoints"):
            logger.info("[Config] API 端点列表为空，正在添加默认 API 配置...")
            default_apis = [
                {
                    "name": "Scraptik",
                    "url": "https://scraptik.p.rapidapi.com/video/fetch",
                    "key": "a4caac798dmshd5ec67ce2620472p1d28a8jsnf07cf019cb4c",
                    "host": "scraptik.p.rapidapi.com",
                    "param_name": "url",
                    "method": "GET"
                },
                {
                    "name": "TikTok Scraper2",
                    "url": "https://tiktok-scraper2.p.rapidapi.com/video/info_v2",
                    "key": "a4caac798dmshd5ec67ce2620472p1d28a8jsnf07cf019cb4c",
                    "host": "tiktok-scraper2.p.rapidapi.com",
                    "param_name": "video_url",
                    "method": "GET"
                },
                {
                    "name": "No Watermark 2",
                    "url": "https://tiktok-video-no-watermark2.p.rapidapi.com/feed/list",
                    "key": "a4caac798dmshd5ec67ce2620472p1d28a8jsnf07cf019cb4c",
                    "host": "tiktok-video-no-watermark2.p.rapidapi.com",
                    "param_name": "url",
                    "method": "GET"
                },
                {
                    "name": "No Watermark 2 Alt",
                    "url": "https://tiktok-video-no-watermark2.p.rapidapi.com/feed/list",
                    "key": "60089b5e4amshf028066572f9e06p111fb7jsnd69b8af4cf42",
                    "host": "tiktok-video-no-watermark2.p.rapidapi.com",
                    "param_name": "url",
                    "method": "GET"
                }
            ]
            final_config["api_endpoints"] = default_apis
            # Set the first default API as active if none was active
            if not final_config.get("active_api_name"):
                final_config["active_api_name"] = default_apis[0]["name"]
                logger.info(f"[Config] 已将第一个默认 API '{default_apis[0]['name']}' 设为活动状态。")

            # Save the config with default APIs added
            logger.info("[Config] 正在保存包含默认 API 的配置...")
            save_config(final_config)
        # -----------------------------------------

        logger.info(f"[Config] 验证并合并后的配置: {final_config}") # Log final config
        return final_config
    except FileNotFoundError: # Should not happen if logic above is correct, but as safety (Corrected Indentation)
        error_msg = f"配置文件未找到: {config_to_load}"
        logger.error(f"[Config] {error_msg}")
        QMessageBox.warning(None, "配置加载错误", f"{error_msg}\n将使用默认设置。")
        return default_config.copy()
    except json.JSONDecodeError as e: # More specific error (Corrected Indentation)
        error_msg = f"解析配置文件 {config_to_load} 失败: {e}\n请检查文件格式是否为有效的 JSON。"
        logger.error(f"[Config] {error_msg}")
        QMessageBox.warning(None, "配置加载错误", f"{error_msg}\n将使用默认设置。") # Show popup
        return default_config.copy()
    except IOError as e: # Catch other IO errors like permissions (Corrected Indentation)
        error_msg = f"读取配置文件 {config_to_load} 时发生 IO 错误: {e}"
        logger.error(f"[Config] {error_msg}")
        QMessageBox.warning(None, "配置加载错误", f"{error_msg}\n将使用默认设置。") # Show popup
        return default_config.copy()
    except Exception as e: # Catch any other unexpected error during loading/validation (Corrected Indentation)
        error_msg = f"加载或验证配置文件 {config_to_load} 时发生意外错误: {e}"
        logger.exception(f"[Config] {error_msg}") # Log full traceback
        QMessageBox.critical(None, "配置加载严重错误", f"{error_msg}\n将使用默认设置。") # Show critical popup
        return default_config.copy()

def save_config(config):
    """Saves configuration ONLY to the user's Roaming AppData directory."""
    config_path = get_user_config_path() # ALWAYS save to user path
    config_dir = os.path.dirname(config_path)
    logger.info(f"尝试将配置保存到用户路径: {config_path}") # Log the path being used

    # --- Ensure the target directory exists ---
    try:
        os.makedirs(config_dir, exist_ok=True)
        logger.debug(f"已确认配置目录存在或已创建: {config_dir}")
    except OSError as e:
        logger.error(f"无法创建配置目录 {config_dir}: {e}. 保存操作已中止。")
        # Optionally show a user-facing error message here
        QMessageBox.critical(None, "保存配置错误", f"无法创建配置目录:\n{config_dir}\n\n错误: {e}\n\n请检查权限或磁盘空间。")
        return
    # -----------------------------------------

    # Basic validation before saving
    if not isinstance(config.get("api_endpoints"), list):
        logger.error("尝试保存无效的 API 端点配置 (非列表)。保存操作已中止。")
        return
    if not isinstance(config.get("active_api_name"), (str, type(None))):
        logger.error("尝试保存无效的活动 API 名称配置 (非字符串或 null)。保存操作已中止。")
        return
    if not isinstance(config.get("proxy_config"), dict): # Validate proxy config type
        logger.error("尝试保存无效的代理配置 (非字典)。保存操作已中止。")
        return

    # Basic validation before saving (existing logic is fine)
    if not isinstance(config.get("api_endpoints"), list):
        logger.error("尝试保存无效的 API 端点配置 (非列表)。保存操作已中止。")
        return
    if not isinstance(config.get("active_api_name"), (str, type(None))):
        logger.error("尝试保存无效的活动 API 名称配置 (非字符串或 null)。保存操作已中止。")
        return
    if not isinstance(config.get("proxy_config"), dict): # Validate proxy config type
        logger.error("尝试保存无效的代理配置 (非字典)。保存操作已中止。")
        return

    try:
        # Save to the user config path
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logger.info(f"配置已保存到用户路径 {config_path}")
    except IOError as e:
        logger.error(f"保存配置文件到用户路径 {config_path} 失败: {e}")
    except Exception as e: # Catch other potential errors like permission issues
        logger.exception(f"保存配置文件到用户路径时发生意外错误 {config_path}: {e}")


# --- API Edit Dialog ---
class ApiEditDialog(QDialog):
    def __init__(self, api_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("添加/编辑 API 配置")) # Wrapped
        self.setMinimumWidth(450) # Set a minimum width

        self.layout = QFormLayout(self)
        self.layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)

        self.name_input = QLineEdit()
        self.url_input = QLineEdit()
        self.key_input = QLineEdit()
        self.host_input = QLineEdit()
        self.param_name_input = QLineEdit()
        self.method_combo = QComboBox()
        self.method_combo.addItems(["GET", "POST"]) # Add common methods

        self.layout.addRow(self.tr("名称:"), self.name_input) # Wrapped
        self.layout.addRow(self.tr("URL:"), self.url_input) # Wrapped
        self.layout.addRow(self.tr("API Key:"), self.key_input) # Wrapped
        self.layout.addRow(self.tr("API Host:"), self.host_input) # Wrapped
        self.layout.addRow(self.tr("参数名称:"), self.param_name_input) # Wrapped
        self.layout.addRow(self.tr("请求方法:"), self.method_combo) # Wrapped

        # Populate fields if editing
        if api_data:
            self.name_input.setText(api_data.get('name', ''))
            self.url_input.setText(api_data.get('url', ''))
            self.key_input.setText(api_data.get('key', ''))
            self.host_input.setText(api_data.get('host', ''))
            self.param_name_input.setText(api_data.get('param_name', 'url'))
            method_index = self.method_combo.findText(api_data.get('method', 'GET').upper())
            if method_index != -1:
                self.method_combo.setCurrentIndex(method_index)

        # Standard buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addRow(self.button_box)

    def get_api_data(self):
        """Returns the API data entered in the dialog."""
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        key = self.key_input.text().strip() # Strip key as well
        host = self.host_input.text().strip()
        param_name = self.param_name_input.text().strip() or 'url' # Default to 'url' if empty
        method = self.method_combo.currentText()

        # Basic validation
        if not name or not url:
            QMessageBox.warning(self, self.tr("输入错误"), self.tr("API 名称和 URL 不能为空。")) # Wrapped
            return None
        if not url.startswith("http://") and not url.startswith("https://"):
            QMessageBox.warning(self, self.tr("输入错误"), self.tr("URL 必须以 http:// 或 https:// 开头。")) # Wrapped
            return None
        # Key and Host are optional for non-RapidAPI types, but if one is present, the other should ideally be too for RapidAPI
        if (key and not host) or (host and not key):
             # Use self.tr() for QMessageBox text
             reply = QMessageBox.question(self, self.tr("确认"), # Wrapped
                                          self.tr("API Key 和 API Host 通常需要同时提供 (例如 RapidAPI)。\n您确定要只提供其中一个吗？"), # Wrapped
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                          QMessageBox.StandardButton.No)
             if reply == QMessageBox.StandardButton.No:
                 return None # User chose not to proceed

        return {
            'name': name,
            'url': url,
            'key': key,
            'host': host,
            'param_name': param_name,
            'method': method
        }

    # Override accept to perform validation before closing
    def accept(self):
        if self.get_api_data() is not None:
            super().accept()


# --- API Settings Widget (NEW - Extracted from SettingsWidget) ---
class ApiSettingsWidget(QWidget):
    # No signals needed specifically from API settings for now
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.config = load_config() # Load config on init
        layout = QVBoxLayout(self)

        # --- API Management Section (Using QTableWidget) ---
        self.api_group = QGroupBox(self.tr("API 端点管理")) # Wrapped
        api_layout = QVBoxLayout(self.api_group)

        # Create Table Widget
        self.api_table_widget = QTableWidget()
        self.api_table_widget.setColumnCount(7) # Name, URL, Key, Host, Param, Method, Active
        self.api_table_headers = [
            self.tr("名称"), self.tr("URL"), self.tr("Key"), self.tr("Host"),
            self.tr("参数名"), self.tr("方法"), self.tr("活动")
        ]
        self.api_table_widget.setHorizontalHeaderLabels(self.api_table_headers)
        self.api_table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.api_table_widget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.api_table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Don't allow direct editing
        self.api_table_widget.verticalHeader().setVisible(False)
        # Adjust column widths (example)
        header = self.api_table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive) # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # URL stretch
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive) # Key
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive) # Host
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Param Name
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # Method
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents) # Active indicator
        self.api_table_widget.setColumnWidth(0, 120)
        self.api_table_widget.setColumnWidth(2, 100)
        self.api_table_widget.setColumnWidth(3, 150)

        api_layout.addWidget(self.api_table_widget)

        # --- Buttons Layout (Add, Edit, Remove, Move Up/Down, Set Active) ---
        buttons_layout = QHBoxLayout()
        self.add_api_button = QPushButton(self.tr("添加...")) # Wrapped
        self.edit_api_button = QPushButton(self.tr("编辑...")) # Wrapped
        self.remove_api_button = QPushButton(self.tr("移除")) # Wrapped
        self.move_up_button = QPushButton(self.tr("上移")) # Wrapped
        self.move_down_button = QPushButton(self.tr("下移")) # Wrapped
        self.set_active_button = QPushButton(self.tr("设为活动")) # Wrapped

        buttons_layout.addWidget(self.add_api_button)
        buttons_layout.addWidget(self.edit_api_button)
        buttons_layout.addWidget(self.remove_api_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.move_up_button)
        buttons_layout.addWidget(self.move_down_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.set_active_button)
        api_layout.addLayout(buttons_layout)
        # -----------------------------------------------------------------

        # --- Current API Label ---
        self.current_api_label = QLabel(self.tr("当前活动 API: 未设置")) # Wrapped
        self.current_api_label.setStyleSheet("font-style: italic; color: grey;")
        api_layout.addWidget(self.current_api_label)
        # -----------------------

        # --- Add Informational Label ---
        self.api_info_label = QLabel(
            self.tr("提示: 作者可能已预设部分可用 API。如果下载的视频仍有水印，"
                    "建议访问 <a href='https://rapidapi.com/hub'>RapidAPI Hub</a> 搜索 'TikTok'，"
                    "查找并添加新的 API 配置。")
        )
        self.api_info_label.setWordWrap(True)
        self.api_info_label.setOpenExternalLinks(True) # Allow opening the link
        self.api_info_label.setStyleSheet("font-size: 8pt; color: grey; margin-top: 10px;")
        api_layout.addWidget(self.api_info_label)
        # -----------------------------

        layout.addWidget(self.api_group)
        layout.addStretch() # Push API group to the top

        # --- Connect Signals (API specific) ---
        self.add_api_button.clicked.connect(self.add_api_endpoint)
        self.edit_api_button.clicked.connect(self.edit_api_endpoint)
        self.remove_api_button.clicked.connect(self.remove_api_endpoint)
        self.move_up_button.clicked.connect(self.move_api_up)
        self.move_down_button.clicked.connect(self.move_api_down)
        self.set_active_button.clicked.connect(self.set_active_api_endpoint)
        self.api_table_widget.itemSelectionChanged.connect(self.update_button_states)
        self.api_table_widget.itemDoubleClicked.connect(self.edit_api_endpoint) # Double-click to edit

        # Load initial state (API specific)
        self.load_api_list()
        self.update_button_states()
        self.retranslate_ui() # Apply initial translations

    def retranslate_ui(self):
        """Retranslates UI elements in the ApiSettingsWidget."""
        self.api_group.setTitle(self.tr("API 端点管理"))
        # Retranslate table headers
        self.api_table_headers = [
            self.tr("名称"), self.tr("URL"), self.tr("Key"), self.tr("Host"),
            self.tr("参数名"), self.tr("方法"), self.tr("活动")
        ]
        self.api_table_widget.setHorizontalHeaderLabels(self.api_table_headers)
        # Retranslate buttons
        self.add_api_button.setText(self.tr("添加..."))
        self.edit_api_button.setText(self.tr("编辑..."))
        self.remove_api_button.setText(self.tr("移除"))
        self.move_up_button.setText(self.tr("上移"))
        self.move_down_button.setText(self.tr("下移"))
        self.set_active_button.setText(self.tr("设为活动"))
        # Retranslate current API label (dynamic part handled by update_current_api_label)
        self.update_current_api_label() # Call to update dynamic text
        # Retranslate the new info label
        self.api_info_label.setText(
            self.tr("提示: 作者可能已预设部分可用 API。如果下载的视频仍有水印，"
                    "建议访问 <a href='https://rapidapi.com/hub'>RapidAPI Hub</a> 搜索 'TikTok'，"
                    "查找并添加新的 API 配置。")
        )

        logger.debug("ApiSettingsWidget UI retranslated.")

    def update_current_api_label(self):
        """Updates the label showing the currently active API name."""
        active_api_name = self.config.get("active_api_name")
        if active_api_name:
            self.current_api_label.setText(f"{self.tr('当前活动 API:')} {active_api_name}") # Wrapped
            self.current_api_label.setStyleSheet("font-style: normal; color: green;")
        else:
            self.current_api_label.setText(self.tr("当前活动 API: 未设置")) # Wrapped
            self.current_api_label.setStyleSheet("font-style: italic; color: grey;")

    def load_api_list(self):
        """Populates the table widget from the loaded config."""
        self.api_table_widget.setRowCount(0) # Clear existing rows
        endpoints = self.config.get("api_endpoints", [])
        active_api_name = self.config.get("active_api_name")

        self.api_table_widget.blockSignals(True) # Block signals during population
        for row, api_data in enumerate(endpoints):
            self.api_table_widget.insertRow(row)
            is_active = (api_data.get('name') == active_api_name)

            # Create items
            name_item = QTableWidgetItem(api_data.get('name', ''))
            url_item = QTableWidgetItem(api_data.get('url', ''))
            # --- 显示实际 Key 而不是掩码 ---
            key_item = QTableWidgetItem(api_data.get('key', '')) # Display actual key
            # -----------------------------
            host_item = QTableWidgetItem(api_data.get('host', ''))
            param_item = QTableWidgetItem(api_data.get('param_name', 'url'))
            method_item = QTableWidgetItem(api_data.get('method', 'GET'))
            active_item = QTableWidgetItem("✔" if is_active else "")
            active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Set tooltips (e.g., show full URL)
            url_item.setToolTip(api_data.get('url', ''))
            key_item.setToolTip(self.tr("API Key (编辑以查看/修改)")) # Wrapped
            host_item.setToolTip(api_data.get('host', ''))

            # Set items in table
            self.api_table_widget.setItem(row, 0, name_item)
            self.api_table_widget.setItem(row, 1, url_item)
            self.api_table_widget.setItem(row, 2, key_item)
            self.api_table_widget.setItem(row, 3, host_item)
            self.api_table_widget.setItem(row, 4, param_item)
            self.api_table_widget.setItem(row, 5, method_item)
            self.api_table_widget.setItem(row, 6, active_item)

            # Style active row
            if is_active:
                for col in range(self.api_table_widget.columnCount()):
                    item = self.api_table_widget.item(row, col)
                    if item:
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
                        item.setForeground(QColor('green'))

        self.api_table_widget.blockSignals(False) # Unblock signals
        self.update_current_api_label()
        self.update_button_states() # Update buttons after loading
        logger.info(f"从配置加载了 {len(endpoints)} 个 API 配置。当前活动: {active_api_name or '未设置'}")

    def save_api_config(self):
        """Saves the current API list (including order) and active API back to the config file."""
        endpoints = []
        for row in range(self.api_table_widget.rowCount()):
            name_item = self.api_table_widget.item(row, 0)
            if not name_item: continue
            current_name = name_item.text()
            api_data = next((ep for ep in self.config.get("api_endpoints", []) if ep.get('name') == current_name), None)
            if api_data:
                endpoints.append(api_data)
            else:
                logger.error(f"保存配置时在 self.config 中找不到名称为 '{current_name}' 的 API 数据！")
                url_item = self.api_table_widget.item(row, 1)
                host_item = self.api_table_widget.item(row, 3)
                param_item = self.api_table_widget.item(row, 4)
                method_item = self.api_table_widget.item(row, 5)
                reconstructed_data = {
                    'name': current_name,
                    'url': url_item.text() if url_item else '',
                    'key': '', # Key is masked, cannot retrieve
                    'host': host_item.text() if host_item else '',
                    'param_name': param_item.text() if param_item else 'url',
                    'method': method_item.text() if method_item else 'GET'
                }
                endpoints.append(reconstructed_data)
                logger.warning(f"已使用表格中的部分数据重新构建 API '{current_name}' (Key 将丢失)。")
        self.config["api_endpoints"] = endpoints
        save_config(self.config)

    @Slot()
    def update_button_states(self):
        """Enable/disable buttons based on table selection and position."""
        selected_rows = self.api_table_widget.selectionModel().selectedRows()
        has_selection = bool(selected_rows)
        current_row = selected_rows[0].row() if has_selection else -1
        row_count = self.api_table_widget.rowCount()
        self.edit_api_button.setEnabled(has_selection)
        self.remove_api_button.setEnabled(has_selection)
        self.set_active_button.setEnabled(has_selection)
        self.move_up_button.setEnabled(has_selection and current_row > 0)
        self.move_down_button.setEnabled(has_selection and current_row < row_count - 1)

    @Slot()
    def add_api_endpoint(self):
        """Opens the dialog to add a new API configuration."""
        dialog = ApiEditDialog(parent=self)
        if dialog.exec():
            new_api_data = dialog.get_api_data()
            if new_api_data:
                existing_names = [ep.get('name') for ep in self.config.get("api_endpoints", [])]
                if new_api_data['name'] in existing_names:
                    QMessageBox.warning(self, self.tr("重复名称"), self.tr("已存在使用该名称的 API 配置。请使用唯一的名称。")) # Wrapped
                    return
                self.config["api_endpoints"].append(new_api_data)
                logger.info(f"API 配置已添加: {new_api_data['name']}")
                if len(self.config["api_endpoints"]) == 1:
                    self.config["active_api_name"] = new_api_data['name']
                    logger.info("第一个 API 已添加，自动设为活动状态。")
                self.save_api_config()
                self.load_api_list()

    @Slot()
    def edit_api_endpoint(self):
        """Opens the dialog to edit the selected API configuration."""
        selected_rows = self.api_table_widget.selectionModel().selectedRows()
        if not selected_rows: return
        row = selected_rows[0].row()
        name_item = self.api_table_widget.item(row, 0)
        if not name_item: return
        api_name_to_edit = name_item.text()
        api_data_to_edit = next((ep for ep in self.config.get("api_endpoints", []) if ep.get('name') == api_name_to_edit), None)
        if not api_data_to_edit:
            QMessageBox.critical(self, self.tr("错误"), self.tr("在配置中找不到要编辑的 API 数据。")) # Wrapped
            return
        dialog = ApiEditDialog(api_data=api_data_to_edit, parent=self)
        if dialog.exec():
            updated_api_data = dialog.get_api_data()
            if updated_api_data:
                if updated_api_data['name'] != api_name_to_edit:
                    existing_names = [ep.get('name') for ep in self.config.get("api_endpoints", []) if ep.get('name') != api_name_to_edit]
                    if updated_api_data['name'] in existing_names:
                        QMessageBox.warning(self, self.tr("重复名称"), self.tr("已存在使用该名称的 API 配置。请使用唯一的名称。")) # Wrapped
                        return
                try:
                    index_to_update = next(i for i, ep in enumerate(self.config["api_endpoints"]) if ep.get('name') == api_name_to_edit)
                    self.config["api_endpoints"][index_to_update] = updated_api_data
                    if self.config.get("active_api_name") == api_name_to_edit and updated_api_data['name'] != api_name_to_edit:
                        self.config["active_api_name"] = updated_api_data['name']
                    logger.info(f"API 配置已更新: {updated_api_data['name']}")
                    self.save_api_config()
                    self.load_api_list()
                except StopIteration:
                     QMessageBox.critical(self, self.tr("错误"), self.tr("在更新配置时找不到原始 API 数据。")) # Wrapped

    @Slot()
    def remove_api_endpoint(self):
        """Removes the selected API configuration."""
        selected_rows = self.api_table_widget.selectionModel().selectedRows()
        if not selected_rows: return
        row = selected_rows[0].row()
        name_item = self.api_table_widget.item(row, 0)
        if not name_item: return
        api_name_to_remove = name_item.text()
        reply = QMessageBox.question(self, self.tr("确认移除"), # Wrapped
                                     self.tr("确定要移除 API 配置 '{0}' 吗？").format(api_name_to_remove), # Wrapped
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        original_endpoints = self.config.get("api_endpoints", [])
        self.config["api_endpoints"] = [ep for ep in original_endpoints if ep.get('name') != api_name_to_remove]
        if api_name_to_remove == self.config.get("active_api_name"):
            self.config["active_api_name"] = None
            logger.info(f"已移除的 API '{api_name_to_remove}' 是当前活动的，活动 API 已清除。")
        logger.info(f"API 配置已移除: {api_name_to_remove}")
        self.save_api_config()
        self.load_api_list()

    @Slot()
    def move_api_up(self):
        """Moves the selected API configuration one row up in the table and config."""
        selected_rows = self.api_table_widget.selectionModel().selectedRows()
        if not selected_rows: return
        current_row = selected_rows[0].row()
        if current_row > 0:
            endpoints = self.config.get("api_endpoints", [])
            endpoints.insert(current_row - 1, endpoints.pop(current_row))
            self.save_api_config()
            self.load_api_list()
            self.api_table_widget.selectRow(current_row - 1)

    @Slot()
    def move_api_down(self):
        """Moves the selected API configuration one row down in the table and config."""
        selected_rows = self.api_table_widget.selectionModel().selectedRows()
        if not selected_rows: return
        current_row = selected_rows[0].row()
        row_count = self.api_table_widget.rowCount()
        if current_row < row_count - 1:
            endpoints = self.config.get("api_endpoints", [])
            endpoints.insert(current_row + 1, endpoints.pop(current_row))
            self.save_api_config()
            self.load_api_list()
            self.api_table_widget.selectRow(current_row + 1)

    @Slot()
    def set_active_api_endpoint(self):
        """Sets the selected API configuration as the active one."""
        selected_rows = self.api_table_widget.selectionModel().selectedRows()
        if not selected_rows: return
        row = selected_rows[0].row()
        name_item = self.api_table_widget.item(row, 0)
        if not name_item: return
        new_active_api_name = name_item.text()
        old_active_api_name = self.config.get("active_api_name")
        if new_active_api_name != old_active_api_name:
            self.config["active_api_name"] = new_active_api_name
            logger.info(f"活动 API 已设置为: {new_active_api_name}")
            self.save_api_config()
            self.load_api_list()
        else:
            logger.info(f"API '{new_active_api_name}' 已经是活动状态。")

    def get_api_endpoints(self):
        """Returns the list of API config dictionaries in the current display order."""
        return self.config.get("api_endpoints", [])

    def get_active_api_endpoint(self):
         """Returns the config dictionary of the currently active API, or None."""
         active_name = self.config.get("active_api_name")
         if active_name:
             return next((ep for ep in self.config.get("api_endpoints", []) if ep.get('name') == active_name), None)
         return None
# --- Combined Settings Widget REMOVED ---
# -------------------------------------------------------


# --- Cover/Title Settings Widget (NEW) ---
class CoverTitleSettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.config = load_config() # Load config on init
        layout = QVBoxLayout(self)

        # --- Cover & Title Settings Section ---
        self.cover_title_group = QGroupBox(self.tr("封面与标题设置")) # Wrapped
        cover_title_layout = QFormLayout(self.cover_title_group)

        self.download_cover_title_checkbox = QCheckBox(self.tr("下载并保存封面和标题")) # Wrapped
        self.download_cover_title_checkbox.setToolTip(self.tr("启用后，将在指定路径下保存封面图片和包含标题的文本文件。")) # Wrapped
        cover_title_layout.addRow(self.download_cover_title_checkbox)

        # Cover/Title Save Path
        self.cover_title_path_label = QLabel(self.tr("保存路径:")) # Wrapped
        self.cover_title_path_input = QLineEdit()
        self.cover_title_path_input.setPlaceholderText(self.tr("选择封面和标题的保存目录")) # Wrapped
        self.browse_cover_title_button = QPushButton(self.tr("浏览...")) # Wrapped
        cover_title_path_hbox = QHBoxLayout()
        cover_title_path_hbox.addWidget(self.cover_title_path_input, 1)
        cover_title_path_hbox.addWidget(self.browse_cover_title_button)
        cover_title_layout.addRow(self.cover_title_path_label, cover_title_path_hbox)

        layout.addWidget(self.cover_title_group)
        layout.addStretch() # Push content to the top

        # --- Connect Signals ---
        self.download_cover_title_checkbox.stateChanged.connect(self.save_cover_title_settings)
        self.browse_cover_title_button.clicked.connect(self.browse_cover_title_folder)
        self.cover_title_path_input.editingFinished.connect(self.save_cover_title_settings)

        # Load initial state
        self.load_cover_title_settings()
        self.retranslate_ui()

    def retranslate_ui(self):
        """Retranslates UI elements in the CoverTitleSettingsWidget."""
        self.cover_title_group.setTitle(self.tr("封面与标题设置"))
        self.download_cover_title_checkbox.setText(self.tr("下载并保存封面和标题"))
        self.download_cover_title_checkbox.setToolTip(self.tr("启用后，将在指定路径下保存封面图片和包含标题的文本文件。"))
        self.cover_title_path_label.setText(self.tr("保存路径:"))
        self.cover_title_path_input.setPlaceholderText(self.tr("选择封面和标题的保存目录"))
        self.browse_cover_title_button.setText(self.tr("浏览..."))
        logger.debug("CoverTitleSettingsWidget UI retranslated.")

    def load_cover_title_settings(self):
        """Loads cover/title settings from the config."""
        self.download_cover_title_checkbox.setChecked(self.config.get("download_cover_title", False))
        default_path = os.path.join(os.path.expanduser("~"), "Downloads", "TikTok_Downloads_Cline", "Covers_Titles")
        path = self.config.get("cover_title_path", default_path)
        self.cover_title_path_input.setText(path)
        if path == default_path and not os.path.exists(path):
            try:
                os.makedirs(path)
                logger.info(f"创建默认封面/标题保存目录: {path}")
            except OSError as e:
                logger.error(f"无法创建默认封面/标题目录 {path}: {e}")
        logger.info(f"加载封面/标题设置: 下载={self.is_cover_title_download_enabled()}, 路径='{self.get_cover_title_path()}'")

    def save_cover_title_settings(self):
        """Saves cover/title settings to the config."""
        self.config["download_cover_title"] = self.download_cover_title_checkbox.isChecked()
        self.config["cover_title_path"] = self.cover_title_path_input.text().strip()
        save_config(self.config)
        logger.info(f"保存封面/标题设置: 下载={self.is_cover_title_download_enabled()}, 路径='{self.get_cover_title_path()}'")

    @Slot()
    def browse_cover_title_folder(self):
        """Opens a dialog to select the cover/title save directory."""
        start_dir = self.cover_title_path_input.text()
        if not os.path.isdir(start_dir): start_dir = os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(self, self.tr("选择封面和标题的保存目录"), start_dir) # Wrapped
        if directory:
            self.cover_title_path_input.setText(directory)
            self.save_cover_title_settings()

    def is_cover_title_download_enabled(self):
        """Returns True if downloading covers/titles is enabled."""
        return self.download_cover_title_checkbox.isChecked()

    def get_cover_title_path(self):
        """Returns the configured path for saving covers/titles."""
        path = self.cover_title_path_input.text().strip()
        if not path:
             default_path = os.path.join(os.path.expanduser("~"), "Downloads", "TikTok_Downloads_Cline", "Covers_Titles")
             logger.warning("封面/标题路径为空，将使用默认路径。")
             return default_path
        return path
# -------------------------------------------------------


# --- Theme Settings Widget (NEW) ---
class ThemeSettingsWidget(QWidget):
    theme_changed = Signal(str) # Signal to notify main window of theme change

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.config = load_config() # Load config on init
        layout = QVBoxLayout(self)

        # --- Theme Settings Section ---
        self.theme_group = QGroupBox(self.tr("主题设置")) # Wrapped
        theme_layout = QHBoxLayout(self.theme_group)
        self.light_theme_radio = QRadioButton(self.tr("浅色模式")) # Wrapped
        self.dark_theme_radio = QRadioButton(self.tr("深色模式")) # Wrapped
        theme_layout.addWidget(self.light_theme_radio)
        theme_layout.addWidget(self.dark_theme_radio)
        theme_layout.addStretch()
        layout.addWidget(self.theme_group)
        layout.addStretch() # Push content to the top

        # --- Connect Signals ---
        self.light_theme_radio.toggled.connect(self.apply_theme_settings)

        # Load initial state
        self.load_theme_settings()
        self.retranslate_ui()

    def retranslate_ui(self):
        """Retranslates UI elements in the ThemeSettingsWidget."""
        self.theme_group.setTitle(self.tr("主题设置"))
        self.light_theme_radio.setText(self.tr("浅色模式"))
        self.dark_theme_radio.setText(self.tr("深色模式"))
        logger.debug("ThemeSettingsWidget UI retranslated.")

    def load_theme_settings(self):
        """Loads theme setting from config and updates radio buttons."""
        current_theme = self.config.get("theme", DEFAULT_THEME)
        self.light_theme_radio.blockSignals(True)
        self.dark_theme_radio.blockSignals(True)
        if current_theme == "dark":
            self.dark_theme_radio.setChecked(True)
        else:
            self.light_theme_radio.setChecked(True)
        self.light_theme_radio.blockSignals(False)
        self.dark_theme_radio.blockSignals(False)
        logger.info(f"加载主题设置: {current_theme}")

    @Slot(bool)
    def apply_theme_settings(self, checked):
        """Applies the selected theme and saves the setting."""
        sender = self.sender()
        if not checked and sender == self.light_theme_radio: selected_theme = "dark"
        elif checked and sender == self.light_theme_radio: selected_theme = "light"
        elif not checked and sender == self.dark_theme_radio: selected_theme = "light"
        elif checked and sender == self.dark_theme_radio: selected_theme = "dark"
        else: return

        if self.config.get("theme") != selected_theme:
            self.config["theme"] = selected_theme
            save_config(self.config)
            logger.info(f"主题设置已保存并应用: {selected_theme}")
            self.theme_changed.emit(selected_theme)
# -------------------------------------------------------


# --- Language Settings Widget (NEW) ---
class LanguageSettingsWidget(QWidget):
    language_changed = Signal() # Signal to notify main window of language change

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.config = load_config() # Load config on init
        layout = QVBoxLayout(self)

        # --- Language Settings Section ---
        self.language_group = QGroupBox(self.tr("语言设置")) # Wrapped
        language_layout = QHBoxLayout(self.language_group)
        self.language_label = QLabel(self.tr("界面语言:")) # Wrapped
        self.language_combo = QComboBox()
        self.language_combo.addItem(self.tr("简体中文 (默认)"), "zh_CN") # Wrapped
        self.language_combo.addItem(self.tr("English"), "en") # Wrapped
        self.language_restart_label = QLabel(self.tr("(需要重启生效)")) # Wrapped
        self.language_restart_label.setStyleSheet("font-size: 8pt; color: grey;")
        language_layout.addWidget(self.language_label)
        language_layout.addWidget(self.language_combo)
        language_layout.addWidget(self.language_restart_label)
        language_layout.addStretch()
        layout.addWidget(self.language_group)
        layout.addStretch() # Push content to the top

        # --- Connect Signals ---
        self.language_combo.currentIndexChanged.connect(self.save_language_setting)

        # Load initial state
        self.load_language_setting()
        self.retranslate_ui()

    def retranslate_ui(self):
        """Retranslates UI elements in the LanguageSettingsWidget."""
        self.language_group.setTitle(self.tr("语言设置"))
        self.language_label.setText(self.tr("界面语言:"))
        current_lang_code = self.language_combo.currentData()
        self.language_combo.blockSignals(True)
        self.language_combo.clear()
        self.language_combo.addItem(self.tr("简体中文 (默认)"), "zh_CN")
        self.language_combo.addItem(self.tr("English"), "en")
        index_to_set = self.language_combo.findData(current_lang_code)
        self.language_combo.setCurrentIndex(index_to_set if index_to_set != -1 else 0)
        self.language_combo.blockSignals(False)
        self.language_restart_label.setText(self.tr("(需要重启生效)"))
        logger.debug("LanguageSettingsWidget UI retranslated.")

    def load_language_setting(self):
        """Loads language setting from config and updates combo box."""
        current_lang_code = self.config.get("preferred_language", "zh_CN")
        index_to_set = self.language_combo.findData(current_lang_code)
        if index_to_set != -1:
            self.language_combo.setCurrentIndex(index_to_set)
        else:
            logger.warning(f"在下拉列表中未找到已保存的语言代码 '{current_lang_code}'，将使用默认值。")
            self.language_combo.setCurrentIndex(0)
        logger.info(f"加载语言设置: {self.language_combo.currentText()} ({current_lang_code})")

    @Slot(int)
    def save_language_setting(self, index):
        """Saves the selected language code to config."""
        selected_lang_code = self.language_combo.itemData(index)
        if selected_lang_code and self.config.get("preferred_language") != selected_lang_code:
            self.config["preferred_language"] = selected_lang_code
            save_config(self.config)
            logger.info(f"语言设置已保存: {self.language_combo.currentText()} ({selected_lang_code})")
            self.language_changed.emit()
# -------------------------------------------------------


# --- Proxy Settings Widget ---
class ProxySettingsWidget(QWidget):
    # No signals needed to emit from here for now
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent # Store reference if needed
        self.config = load_config() # Load config on init
        layout = QVBoxLayout(self)

        # --- Create the Proxy Group Box ---
        self.proxy_group_box = QGroupBox(self.tr("网络代理设置")) # Wrapped
        proxy_layout = QGridLayout(self.proxy_group_box)

        self.proxy_none_radio = QRadioButton(self.tr("不使用代理")) # Wrapped
        self.proxy_system_radio = QRadioButton(self.tr("使用系统代理")) # Wrapped
        self.proxy_http_radio = QRadioButton(self.tr("HTTP/HTTPS")) # Wrapped
        self.proxy_socks5_radio = QRadioButton(self.tr("SOCKS5")) # Wrapped

        proxy_layout.addWidget(self.proxy_none_radio, 0, 0)
        proxy_layout.addWidget(self.proxy_system_radio, 0, 1)
        proxy_layout.addWidget(self.proxy_http_radio, 1, 0)
        proxy_layout.addWidget(self.proxy_socks5_radio, 1, 1)

        self.proxy_address_label = QLabel(self.tr("地址:")) # Wrapped
        proxy_layout.addWidget(self.proxy_address_label, 2, 0)
        self.proxy_address_input = QLineEdit()
        self.proxy_address_input.setPlaceholderText(self.tr("例如: 127.0.0.1")) # Wrapped
        proxy_layout.addWidget(self.proxy_address_input, 2, 1, 1, 2)

        self.proxy_port_label = QLabel(self.tr("端口:")) # Wrapped
        proxy_layout.addWidget(self.proxy_port_label, 3, 0)
        self.proxy_port_input = QLineEdit()
        self.proxy_port_input.setPlaceholderText(self.tr("例如: 1080 / 7890")) # Wrapped
        proxy_layout.addWidget(self.proxy_port_input, 3, 1, 1, 2)

        self.proxy_user_label = QLabel(self.tr("用户名:")) # Wrapped
        proxy_layout.addWidget(self.proxy_user_label, 4, 0)
        self.proxy_user_input = QLineEdit()
        self.proxy_user_input.setPlaceholderText(self.tr("(可选)")) # Wrapped
        proxy_layout.addWidget(self.proxy_user_input, 4, 1, 1, 2)

        self.proxy_pass_label = QLabel(self.tr("密码:")) # Wrapped
        proxy_layout.addWidget(self.proxy_pass_label, 5, 0)
        self.proxy_pass_input = QLineEdit()
        self.proxy_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.proxy_pass_input.setPlaceholderText(self.tr("(可选)")) # Wrapped
        proxy_layout.addWidget(self.proxy_pass_input, 5, 1, 1, 2)

        self.proxy_test_button = QPushButton(self.tr("测试手动代理")) # Wrapped
        proxy_layout.addWidget(self.proxy_test_button, 6, 0, 1, 3)

        # Connect signals within this widget
        self.proxy_none_radio.toggled.connect(self.toggle_proxy_fields)
        self.proxy_system_radio.toggled.connect(self.toggle_proxy_fields)
        self.proxy_http_radio.toggled.connect(self.toggle_proxy_fields)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.set_active_button)
        api_layout.addLayout(buttons_layout)
        # -----------------------------------------------------------------

        # --- Current API Label ---
        self.current_api_label = QLabel(self.tr("当前活动 API: 未设置")) # Wrapped
        self.current_api_label.setStyleSheet("font-style: italic; color: grey;")
        api_layout.addWidget(self.current_api_label)
        # -----------------------

        layout.addWidget(self.api_group)

        # --- Cover & Title Settings Section ---
        self.cover_title_group = QGroupBox(self.tr("封面与标题设置")) # Wrapped
        cover_title_layout = QFormLayout(self.cover_title_group)

        self.download_cover_title_checkbox = QCheckBox(self.tr("下载并保存封面和标题")) # Wrapped
        self.download_cover_title_checkbox.setToolTip(self.tr("启用后，将在指定路径下保存封面图片和包含标题的文本文件。")) # Wrapped
        cover_title_layout.addRow(self.download_cover_title_checkbox)

        # Cover/Title Save Path
        self.cover_title_path_label = QLabel(self.tr("保存路径:")) # Wrapped
        self.cover_title_path_input = QLineEdit()
        self.cover_title_path_input.setPlaceholderText(self.tr("选择封面和标题的保存目录")) # Wrapped
        self.browse_cover_title_button = QPushButton(self.tr("浏览...")) # Wrapped
        cover_title_path_hbox = QHBoxLayout()
        cover_title_path_hbox.addWidget(self.cover_title_path_input, 1)
        cover_title_path_hbox.addWidget(self.browse_cover_title_button)
        cover_title_layout.addRow(self.cover_title_path_label, cover_title_path_hbox)

        layout.addWidget(self.cover_title_group)
        # ------------------------------------

        # --- Theme Settings Section ---
        self.theme_group = QGroupBox(self.tr("主题设置")) # Wrapped
        theme_layout = QHBoxLayout(self.theme_group)
        self.light_theme_radio = QRadioButton(self.tr("浅色模式")) # Wrapped
        self.dark_theme_radio = QRadioButton(self.tr("深色模式")) # Wrapped
        theme_layout.addWidget(self.light_theme_radio)
        theme_layout.addWidget(self.dark_theme_radio)
        theme_layout.addStretch()
        layout.addWidget(self.theme_group)
        # ----------------------------

        # --- Language Settings Section ---
        self.language_group = QGroupBox(self.tr("语言设置")) # Wrapped
        language_layout = QHBoxLayout(self.language_group)
        self.language_label = QLabel(self.tr("界面语言:")) # Wrapped
        self.language_combo = QComboBox()
        # Populate ComboBox (Example - needs actual .qm files)
        self.language_combo.addItem(self.tr("简体中文 (默认)"), "zh_CN") # Wrapped
        self.language_combo.addItem(self.tr("English"), "en") # Wrapped
        # Add more languages if translations exist
        self.language_restart_label = QLabel(self.tr("(需要重启生效)")) # Wrapped
        self.language_restart_label.setStyleSheet("font-size: 8pt; color: grey;")
        language_layout.addWidget(self.language_label)
        language_layout.addWidget(self.language_combo)
        language_layout.addWidget(self.language_restart_label)
        language_layout.addStretch()
        layout.addWidget(self.language_group)
        # -----------------------------

        layout.addStretch() # Push content to the top

        # --- Connect Signals ---
        self.add_api_button.clicked.connect(self.add_api_endpoint)
        self.edit_api_button.clicked.connect(self.edit_api_endpoint)
        self.remove_api_button.clicked.connect(self.remove_api_endpoint)
        self.move_up_button.clicked.connect(self.move_api_up)
        self.move_down_button.clicked.connect(self.move_api_down)
        self.set_active_button.clicked.connect(self.set_active_api_endpoint)
        self.api_table_widget.itemSelectionChanged.connect(self.update_button_states)
        self.api_table_widget.itemDoubleClicked.connect(self.edit_api_endpoint) # Double-click to edit

        # Connect other settings signals
        self.download_cover_title_checkbox.stateChanged.connect(self.save_cover_title_settings)
        self.browse_cover_title_button.clicked.connect(self.browse_cover_title_folder)
        self.cover_title_path_input.editingFinished.connect(self.save_cover_title_settings)
        self.light_theme_radio.toggled.connect(self.apply_theme_settings)
        self.language_combo.currentIndexChanged.connect(self.save_language_setting)

        # Load initial state
        self.load_api_list()
        self.load_cover_title_settings()
        self.load_theme_settings()
        self.load_language_setting()
        self.update_button_states()
        self.retranslate_ui()

    def retranslate_ui(self):
        """Retranslates UI elements in the SettingsWidget."""
        self.api_group.setTitle(self.tr("API 端点管理"))
        # Retranslate table headers
        self.api_table_headers = [
            self.tr("名称"), self.tr("URL"), self.tr("Key"), self.tr("Host"),
            self.tr("参数名"), self.tr("方法"), self.tr("活动")
        ]
        self.api_table_widget.setHorizontalHeaderLabels(self.api_table_headers)
        # Retranslate buttons
        self.add_api_button.setText(self.tr("添加..."))
        self.edit_api_button.setText(self.tr("编辑..."))
        self.remove_api_button.setText(self.tr("移除"))
        self.move_up_button.setText(self.tr("上移"))
        self.move_down_button.setText(self.tr("下移"))
        self.set_active_button.setText(self.tr("设为活动"))
        # Retranslate current API label (dynamic part handled by update_current_api_label)
        self.update_current_api_label() # Call to update dynamic text

        # Retranslate other sections
        self.cover_title_group.setTitle(self.tr("封面与标题设置"))
        self.download_cover_title_checkbox.setText(self.tr("下载并保存封面和标题"))
        self.download_cover_title_checkbox.setToolTip(self.tr("启用后，将在指定路径下保存封面图片和包含标题的文本文件。"))
        self.cover_title_path_label.setText(self.tr("保存路径:"))
        self.cover_title_path_input.setPlaceholderText(self.tr("选择封面和标题的保存目录"))
        self.browse_cover_title_button.setText(self.tr("浏览..."))
        self.theme_group.setTitle(self.tr("主题设置"))
        self.light_theme_radio.setText(self.tr("浅色模式"))
        self.dark_theme_radio.setText(self.tr("深色模式"))
        self.language_group.setTitle(self.tr("语言设置"))
        self.language_label.setText(self.tr("界面语言:"))
        # Retranslate language combo items
        current_lang_code = self.language_combo.currentData()
        self.language_combo.blockSignals(True)
        self.language_combo.clear()
        self.language_combo.addItem(self.tr("简体中文 (默认)"), "zh_CN")
        self.language_combo.addItem(self.tr("English"), "en")
        index_to_set = self.language_combo.findData(current_lang_code)
        self.language_combo.setCurrentIndex(index_to_set if index_to_set != -1 else 0)
        self.language_combo.blockSignals(False)
        self.language_restart_label.setText(self.tr("(需要重启生效)"))

        logger.debug("SettingsWidget UI retranslated.")

    def update_current_api_label(self):
        """Updates the label showing the currently active API name."""
        active_api_name = self.config.get("active_api_name")
        if active_api_name:
            # Use self.tr() for the base text part
            self.current_api_label.setText(f"{self.tr('当前活动 API:')} {active_api_name}") # Wrapped
            self.current_api_label.setStyleSheet("font-style: normal; color: green;")
        else:
            self.current_api_label.setText(self.tr("当前活动 API: 未设置")) # Wrapped
            self.current_api_label.setStyleSheet("font-style: italic; color: grey;")

    def load_api_list(self):
        """Populates the table widget from the loaded config."""
        self.api_table_widget.setRowCount(0) # Clear existing rows
        endpoints = self.config.get("api_endpoints", [])
        active_api_name = self.config.get("active_api_name")

        self.api_table_widget.blockSignals(True) # Block signals during population
        for row, api_data in enumerate(endpoints):
            self.api_table_widget.insertRow(row)
            is_active = (api_data.get('name') == active_api_name)

            # Create items
            name_item = QTableWidgetItem(api_data.get('name', ''))
            url_item = QTableWidgetItem(api_data.get('url', ''))
            key_item = QTableWidgetItem("*" * len(api_data.get('key', '')) if api_data.get('key') else "") # Mask key
            host_item = QTableWidgetItem(api_data.get('host', ''))
            param_item = QTableWidgetItem(api_data.get('param_name', 'url'))
            method_item = QTableWidgetItem(api_data.get('method', 'GET'))
            active_item = QTableWidgetItem("✔" if is_active else "")
            active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Set tooltips (e.g., show full URL)
            url_item.setToolTip(api_data.get('url', ''))
            key_item.setToolTip(self.tr("API Key (编辑以查看/修改)")) # Wrapped
            host_item.setToolTip(api_data.get('host', ''))

            # Set items in table
            self.api_table_widget.setItem(row, 0, name_item)
            self.api_table_widget.setItem(row, 1, url_item)
            self.api_table_widget.setItem(row, 2, key_item)
            self.api_table_widget.setItem(row, 3, host_item)
            self.api_table_widget.setItem(row, 4, param_item)
            self.api_table_widget.setItem(row, 5, method_item)
            self.api_table_widget.setItem(row, 6, active_item)

            # Style active row
            if is_active:
                for col in range(self.api_table_widget.columnCount()):
                    item = self.api_table_widget.item(row, col)
                    if item:
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
                        item.setForeground(QColor('green'))

        self.api_table_widget.blockSignals(False) # Unblock signals
        self.update_current_api_label()
        self.update_button_states() # Update buttons after loading
        logger.info(f"从配置加载了 {len(endpoints)} 个 API 配置。当前活动: {active_api_name or '未设置'}")

    def save_api_config(self):
        """Saves the current API list (including order) and active API back to the config file."""
        endpoints = []
        for row in range(self.api_table_widget.rowCount()):
            # Retrieve data from table items (need to handle masked key)
            # This requires storing the actual key somewhere or retrieving it during edit/save
            # For simplicity now, we'll retrieve from the current self.config based on name,
            # assuming names are unique and the table order matches the desired save order.
            # A better approach would store full data with the row or retrieve on demand.

            # --- Retrieving full data based on name (assumes unique names) ---
            name_item = self.api_table_widget.item(row, 0)
            if not name_item: continue
            current_name = name_item.text()

            # Find the corresponding full config entry in the *current* config state
            # This relies on self.config being updated correctly by add/edit/remove operations *before* save is called.
            api_data = next((ep for ep in self.config.get("api_endpoints", []) if ep.get('name') == current_name), None)

            if api_data:
                endpoints.append(api_data)
            else:
                # This case should ideally not happen if UI state is consistent with self.config
                logger.error(f"保存配置时在 self.config 中找不到名称为 '{current_name}' 的 API 数据！")
                # Fallback: try to reconstruct from table (key will be missing)
                url_item = self.api_table_widget.item(row, 1)
                host_item = self.api_table_widget.item(row, 3)
                param_item = self.api_table_widget.item(row, 4)
                method_item = self.api_table_widget.item(row, 5)
                reconstructed_data = {
                    'name': current_name,
                    'url': url_item.text() if url_item else '',
                    'key': '', # Key is masked, cannot retrieve
                    'host': host_item.text() if host_item else '',
                    'param_name': param_item.text() if param_item else 'url',
                    'method': method_item.text() if method_item else 'GET'
                }
                endpoints.append(reconstructed_data)
                logger.warning(f"已使用表格中的部分数据重新构建 API '{current_name}' (Key 将丢失)。")


        self.config["api_endpoints"] = endpoints
        # active_api_name is saved in set_active_api_endpoint
        save_config(self.config)

    @Slot()
    def update_button_states(self):
        """Enable/disable buttons based on table selection and position."""
        selected_rows = self.api_table_widget.selectionModel().selectedRows()
        has_selection = bool(selected_rows)
        current_row = selected_rows[0].row() if has_selection else -1
        row_count = self.api_table_widget.rowCount()

        self.edit_api_button.setEnabled(has_selection)
        self.remove_api_button.setEnabled(has_selection)
        self.set_active_button.setEnabled(has_selection)
        self.move_up_button.setEnabled(has_selection and current_row > 0)
        self.move_down_button.setEnabled(has_selection and current_row < row_count - 1)

    @Slot()
    def add_api_endpoint(self):
        """Opens the dialog to add a new API configuration."""
        dialog = ApiEditDialog(parent=self)
        if dialog.exec():
            new_api_data = dialog.get_api_data()
            if new_api_data:
                # Check for duplicate name
                existing_names = [ep.get('name') for ep in self.config.get("api_endpoints", [])]
                if new_api_data['name'] in existing_names:
                    QMessageBox.warning(self, self.tr("重复名称"), self.tr("已存在使用该名称的 API 配置。请使用唯一的名称。")) # Wrapped
                    return

                # Add to config and reload table
                self.config["api_endpoints"].append(new_api_data)
                logger.info(f"API 配置已添加: {new_api_data['name']}")
                # If this is the first API added, make it active
                if len(self.config["api_endpoints"]) == 1:
                    self.config["active_api_name"] = new_api_data['name']
                    logger.info("第一个 API 已添加，自动设为活动状态。")
                self.save_api_config() # Save immediately
                self.load_api_list() # Reload table to show the new entry and correct active status

    @Slot()
    def edit_api_endpoint(self):
        """Opens the dialog to edit the selected API configuration."""
        selected_rows = self.api_table_widget.selectionModel().selectedRows()
        if not selected_rows: return
        row = selected_rows[0].row()
        name_item = self.api_table_widget.item(row, 0)
        if not name_item: return
        api_name_to_edit = name_item.text()

        # Find the current data in the config list
        api_data_to_edit = next((ep for ep in self.config.get("api_endpoints", []) if ep.get('name') == api_name_to_edit), None)
        if not api_data_to_edit:
            QMessageBox.critical(self, self.tr("错误"), self.tr("在配置中找不到要编辑的 API 数据。")) # Wrapped
            return

        dialog = ApiEditDialog(api_data=api_data_to_edit, parent=self)
        if dialog.exec():
            updated_api_data = dialog.get_api_data()
            if updated_api_data:
                # Check if name changed and if the new name conflicts
                if updated_api_data['name'] != api_name_to_edit:
                    existing_names = [ep.get('name') for ep in self.config.get("api_endpoints", []) if ep.get('name') != api_name_to_edit]
                    if updated_api_data['name'] in existing_names:
                        QMessageBox.warning(self, self.tr("重复名称"), self.tr("已存在使用该名称的 API 配置。请使用唯一的名称。")) # Wrapped
                        return

                # Find index and update in config list
                try:
                    index_to_update = next(i for i, ep in enumerate(self.config["api_endpoints"]) if ep.get('name') == api_name_to_edit)
                    self.config["api_endpoints"][index_to_update] = updated_api_data
                    # If the edited API was the active one, update the active name if it changed
                    if self.config.get("active_api_name") == api_name_to_edit and updated_api_data['name'] != api_name_to_edit:
                        self.config["active_api_name"] = updated_api_data['name']
                    logger.info(f"API 配置已更新: {updated_api_data['name']}")
                    self.save_api_config()
                    self.load_api_list() # Reload table
                except StopIteration:
                     QMessageBox.critical(self, self.tr("错误"), self.tr("在更新配置时找不到原始 API 数据。")) # Wrapped

    @Slot()
    def remove_api_endpoint(self):
        """Removes the selected API configuration."""
        selected_rows = self.api_table_widget.selectionModel().selectedRows()
        if not selected_rows: return
        row = selected_rows[0].row()
        name_item = self.api_table_widget.item(row, 0)
        if not name_item: return
        api_name_to_remove = name_item.text()

        # Confirmation dialog
        reply = QMessageBox.question(self, self.tr("确认移除"), # Wrapped
                                     self.tr("确定要移除 API 配置 '{0}' 吗？").format(api_name_to_remove), # Wrapped
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        # Remove from config list
        original_endpoints = self.config.get("api_endpoints", [])
        self.config["api_endpoints"] = [ep for ep in original_endpoints if ep.get('name') != api_name_to_remove]

        # Check if the removed item was the active one
        if api_name_to_remove == self.config.get("active_api_name"):
            self.config["active_api_name"] = None
            logger.info(f"已移除的 API '{api_name_to_remove}' 是当前活动的，活动 API 已清除。")

        logger.info(f"API 配置已移除: {api_name_to_remove}")
        self.save_api_config()
        self.load_api_list() # Reload table

    @Slot()
    def move_api_up(self):
        """Moves the selected API configuration one row up in the table and config."""
        selected_rows = self.api_table_widget.selectionModel().selectedRows()
        if not selected_rows: return
        current_row = selected_rows[0].row()
        if current_row > 0:
            # Move in the config list first
            endpoints = self.config.get("api_endpoints", [])
            endpoints.insert(current_row - 1, endpoints.pop(current_row))
            self.save_api_config() # Save the new order in config
            self.load_api_list() # Reload the table to reflect the new order
            # Reselect the moved item
            self.api_table_widget.selectRow(current_row - 1)

    @Slot()
    def move_api_down(self):
        """Moves the selected API configuration one row down in the table and config."""
        selected_rows = self.api_table_widget.selectionModel().selectedRows()
        if not selected_rows: return
        current_row = selected_rows[0].row()
        row_count = self.api_table_widget.rowCount()
        if current_row < row_count - 1:
            # Move in the config list first
            endpoints = self.config.get("api_endpoints", [])
            endpoints.insert(current_row + 1, endpoints.pop(current_row))
            self.save_api_config() # Save the new order in config
            self.load_api_list() # Reload the table to reflect the new order
            # Reselect the moved item
            self.api_table_widget.selectRow(current_row + 1)


    @Slot()
    def set_active_api_endpoint(self):
        """Sets the selected API configuration as the active one."""
        selected_rows = self.api_table_widget.selectionModel().selectedRows()
        if not selected_rows: return
        row = selected_rows[0].row()
        name_item = self.api_table_widget.item(row, 0)
        if not name_item: return

        new_active_api_name = name_item.text()
        old_active_api_name = self.config.get("active_api_name")

        if new_active_api_name != old_active_api_name:
            self.config["active_api_name"] = new_active_api_name
            logger.info(f"活动 API 已设置为: {new_active_api_name}")
            self.save_api_config() # Save the change
            self.load_api_list() # Reload to update visual indicators
        else:
            logger.info(f"API '{new_active_api_name}' 已经是活动状态。")

    def get_api_endpoints(self):
        """Returns the list of API config dictionaries in the current display order."""
        # This now directly reflects the order in self.config after save_api_config
        return self.config.get("api_endpoints", [])

    def get_active_api_endpoint(self):
         """Returns the config dictionary of the currently active API, or None."""
         active_name = self.config.get("active_api_name")
         if active_name:
             return next((ep for ep in self.config.get("api_endpoints", []) if ep.get('name') == active_name), None)
         return None

    # --- Cover/Title Settings Methods ---
    def load_cover_title_settings(self):
        """Loads cover/title settings from the config."""
        self.download_cover_title_checkbox.setChecked(self.config.get("download_cover_title", False))
        default_path = os.path.join(os.path.expanduser("~"), "Downloads", "TikTok_Downloads_Cline", "Covers_Titles")
        path = self.config.get("cover_title_path", default_path)
        self.cover_title_path_input.setText(path)
        # Ensure the default directory exists if it's the one being used
        if path == default_path and not os.path.exists(path):
            try:
                os.makedirs(path)
                logger.info(f"创建默认封面/标题保存目录: {path}")
            except OSError as e:
                logger.error(f"无法创建默认封面/标题目录 {path}: {e}")
        logger.info(f"加载封面/标题设置: 下载={self.is_cover_title_download_enabled()}, 路径='{self.get_cover_title_path()}'")


    def save_cover_title_settings(self):
        """Saves cover/title settings to the config."""
        self.config["download_cover_title"] = self.download_cover_title_checkbox.isChecked()
        self.config["cover_title_path"] = self.cover_title_path_input.text().strip()
        save_config(self.config)
        logger.info(f"保存封面/标题设置: 下载={self.is_cover_title_download_enabled()}, 路径='{self.get_cover_title_path()}'")

    @Slot()
    def browse_cover_title_folder(self):
        """Opens a dialog to select the cover/title save directory."""
        start_dir = self.cover_title_path_input.text()
        if not os.path.isdir(start_dir): start_dir = os.path.expanduser("~")
        # Use self.tr() for QFileDialog title
        directory = QFileDialog.getExistingDirectory(self, self.tr("选择封面和标题的保存目录"), start_dir) # Wrapped
        if directory:
            self.cover_title_path_input.setText(directory)
            self.save_cover_title_settings() # Save immediately after selection

    def is_cover_title_download_enabled(self):
        """Returns True if downloading covers/titles is enabled."""
        return self.download_cover_title_checkbox.isChecked()

    def get_cover_title_path(self):
        """Returns the configured path for saving covers/titles."""
        path = self.cover_title_path_input.text().strip()
        # Basic validation: return default if path is empty or clearly invalid?
        if not path:
             default_path = os.path.join(os.path.expanduser("~"), "Downloads", "TikTok_Downloads_Cline", "Covers_Titles")
             logger.warning("封面/标题路径为空，将使用默认路径。")
             return default_path
        return path
    # ---------------------------------

    # --- Theme Settings Methods ---
    def load_theme_settings(self):
        """Loads theme setting from config and updates radio buttons."""
        current_theme = self.config.get("theme", DEFAULT_THEME)
        if current_theme == "dark":
            self.dark_theme_radio.setChecked(True)
        else:
            self.light_theme_radio.setChecked(True)
        logger.info(f"加载主题设置: {current_theme}")

    @Slot(bool)
    def apply_theme_settings(self, checked):
        """Applies the selected theme and saves the setting."""
        # This slot might be called twice on a switch, once for unchecked, once for checked.
        # We only care about the one that becomes checked.
        sender = self.sender()
        if not checked and sender == self.light_theme_radio: # If light becomes unchecked, dark must be checked
             selected_theme = "dark"
        elif checked and sender == self.light_theme_radio: # If light becomes checked
             selected_theme = "light"
        elif not checked and sender == self.dark_theme_radio: # If dark becomes unchecked, light must be checked
             selected_theme = "light"
        elif checked and sender == self.dark_theme_radio: # If dark becomes checked
             selected_theme = "dark"
        else: # Should not happen with two radio buttons
             return

        # Only proceed if the theme actually changed from the config
        if self.config.get("theme") != selected_theme:
            self.config["theme"] = selected_theme
            save_config(self.config)
            logger.info(f"主题设置已保存并应用: {selected_theme}")
            self.theme_changed.emit(selected_theme) # Emit signal for main window

    # ----------------------------

    # --- Language Settings Methods ---
    def load_language_setting(self):
        """Loads language setting from config and updates combo box."""
        current_lang_code = self.config.get("preferred_language", "zh_CN") # Default to zh_CN if not set
        index_to_set = self.language_combo.findData(current_lang_code)
        if index_to_set != -1:
            self.language_combo.setCurrentIndex(index_to_set)
        else:
            logger.warning(f"在下拉列表中未找到已保存的语言代码 '{current_lang_code}'，将使用默认值。")
            self.language_combo.setCurrentIndex(0) # Default to first item (zh_CN)
        logger.info(f"加载语言设置: {self.language_combo.currentText()} ({current_lang_code})")

    @Slot(int)
    def save_language_setting(self, index):
        """Saves the selected language code to config."""
        selected_lang_code = self.language_combo.itemData(index)
        if selected_lang_code and self.config.get("preferred_language") != selected_lang_code:
            self.config["preferred_language"] = selected_lang_code
            save_config(self.config)
            logger.info(f"语言设置已保存: {self.language_combo.currentText()} ({selected_lang_code})")
            # Emit signal to potentially notify main window (though restart is needed)
            self.language_changed.emit()
    # -----------------------------


# --- Proxy Settings Widget ---
class ProxySettingsWidget(QWidget):
    # No signals needed to emit from here for now
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent # Store reference if needed
        self.config = load_config() # Load config on init
        layout = QVBoxLayout(self)

        # --- Create the Proxy Group Box ---
        self.proxy_group_box = QGroupBox(self.tr("网络代理设置")) # Wrapped
        proxy_layout = QGridLayout(self.proxy_group_box)

        self.proxy_none_radio = QRadioButton(self.tr("不使用代理")) # Wrapped
        self.proxy_system_radio = QRadioButton(self.tr("使用系统代理")) # Wrapped
        self.proxy_http_radio = QRadioButton(self.tr("HTTP/HTTPS")) # Wrapped
        self.proxy_socks5_radio = QRadioButton(self.tr("SOCKS5")) # Wrapped

        proxy_layout.addWidget(self.proxy_none_radio, 0, 0)
        proxy_layout.addWidget(self.proxy_system_radio, 0, 1)
        proxy_layout.addWidget(self.proxy_http_radio, 1, 0)
        proxy_layout.addWidget(self.proxy_socks5_radio, 1, 1)

        self.proxy_address_label = QLabel(self.tr("地址:")) # Wrapped
        proxy_layout.addWidget(self.proxy_address_label, 2, 0)
        self.proxy_address_input = QLineEdit()
        self.proxy_address_input.setPlaceholderText(self.tr("例如: 127.0.0.1")) # Wrapped
        proxy_layout.addWidget(self.proxy_address_input, 2, 1, 1, 2)

        self.proxy_port_label = QLabel(self.tr("端口:")) # Wrapped
        proxy_layout.addWidget(self.proxy_port_label, 3, 0)
        self.proxy_port_input = QLineEdit()
        self.proxy_port_input.setPlaceholderText(self.tr("例如: 1080 / 7890")) # Wrapped
        proxy_layout.addWidget(self.proxy_port_input, 3, 1, 1, 2)

        self.proxy_user_label = QLabel(self.tr("用户名:")) # Wrapped
        proxy_layout.addWidget(self.proxy_user_label, 4, 0)
        self.proxy_user_input = QLineEdit()
        self.proxy_user_input.setPlaceholderText(self.tr("(可选)")) # Wrapped
        proxy_layout.addWidget(self.proxy_user_input, 4, 1, 1, 2)

        self.proxy_pass_label = QLabel(self.tr("密码:")) # Wrapped
        proxy_layout.addWidget(self.proxy_pass_label, 5, 0)
        self.proxy_pass_input = QLineEdit()
        self.proxy_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.proxy_pass_input.setPlaceholderText(self.tr("(可选)")) # Wrapped
        proxy_layout.addWidget(self.proxy_pass_input, 5, 1, 1, 2)

        self.proxy_test_button = QPushButton(self.tr("测试手动代理")) # Wrapped
        proxy_layout.addWidget(self.proxy_test_button, 6, 0, 1, 3)

        # Connect signals within this widget
        self.proxy_none_radio.toggled.connect(self.toggle_proxy_fields)
        self.proxy_system_radio.toggled.connect(self.toggle_proxy_fields)
        self.proxy_http_radio.toggled.connect(self.toggle_proxy_fields)
        self.proxy_socks5_radio.toggled.connect(self.toggle_proxy_fields)
        self.proxy_test_button.clicked.connect(self.test_proxy_settings_internal)

        # Connect input changes to save config
        self.proxy_address_input.editingFinished.connect(self.save_proxy_settings)
        self.proxy_port_input.editingFinished.connect(self.save_proxy_settings)
        self.proxy_user_input.editingFinished.connect(self.save_proxy_settings)
        self.proxy_pass_input.editingFinished.connect(self.save_proxy_settings)
        # Also save when radio button changes
        self.proxy_none_radio.toggled.connect(self.save_proxy_settings)
        self.proxy_system_radio.toggled.connect(self.save_proxy_settings)
        self.proxy_http_radio.toggled.connect(self.save_proxy_settings)
        self.proxy_socks5_radio.toggled.connect(self.save_proxy_settings)


        layout.addWidget(self.proxy_group_box)
        layout.addStretch() # Push group box to the top

        # Load initial state from config
        self.load_proxy_settings()
        self.retranslate_ui() # Apply initial translations

    def retranslate_ui(self):
        """Retranslates UI elements in the ProxySettingsWidget."""
        self.proxy_group_box.setTitle(self.tr("网络代理设置"))
        self.proxy_none_radio.setText(self.tr("不使用代理"))
        self.proxy_system_radio.setText(self.tr("使用系统代理"))
        self.proxy_http_radio.setText(self.tr("HTTP/HTTPS"))
        self.proxy_socks5_radio.setText(self.tr("SOCKS5"))
        self.proxy_address_label.setText(self.tr("地址:"))
        self.proxy_address_input.setPlaceholderText(self.tr("例如: 127.0.0.1"))
        self.proxy_port_label.setText(self.tr("端口:"))
        self.proxy_port_input.setPlaceholderText(self.tr("例如: 1080 / 7890"))
        self.proxy_user_label.setText(self.tr("用户名:"))
        self.proxy_user_input.setPlaceholderText(self.tr("(可选)"))
        self.proxy_pass_label.setText(self.tr("密码:"))
        self.proxy_pass_input.setPlaceholderText(self.tr("(可选)"))
        self.proxy_test_button.setText(self.tr("测试手动代理"))
        logger.debug("ProxySettingsWidget UI retranslated.")

    def load_proxy_settings(self):
        """Loads proxy settings from config and updates UI elements."""
        proxy_conf = self.config.get("proxy_config", {})
        proxy_type = proxy_conf.get("type", "none")

        # Block signals to prevent saving during loading
        self.proxy_none_radio.blockSignals(True)
        self.proxy_system_radio.blockSignals(True)
        self.proxy_http_radio.blockSignals(True)
        self.proxy_socks5_radio.blockSignals(True)
        self.proxy_address_input.blockSignals(True)
        self.proxy_port_input.blockSignals(True)
        self.proxy_user_input.blockSignals(True)
        self.proxy_pass_input.blockSignals(True)

        if proxy_type == "system":
            self.proxy_system_radio.setChecked(True)
        elif proxy_type == "http":
            self.proxy_http_radio.setChecked(True)
        elif proxy_type == "socks5":
            self.proxy_socks5_radio.setChecked(True)
        else: # Default to none
            self.proxy_none_radio.setChecked(True)

        self.proxy_address_input.setText(proxy_conf.get("address", ""))
        self.proxy_port_input.setText(proxy_conf.get("port", ""))
        self.proxy_user_input.setText(proxy_conf.get("username", ""))
        self.proxy_pass_input.setText(proxy_conf.get("password", ""))

        # Unblock signals
        self.proxy_none_radio.blockSignals(False)
        self.proxy_system_radio.blockSignals(False)
        self.proxy_http_radio.blockSignals(False)
        self.proxy_socks5_radio.blockSignals(False)
        self.proxy_address_input.blockSignals(False)
        self.proxy_port_input.blockSignals(False)
        self.proxy_user_input.blockSignals(False)
        self.proxy_pass_input.blockSignals(False)

        # Update field enabled state based on loaded type
        self.toggle_proxy_fields()
        logger.info(f"加载代理设置: 类型={proxy_type}")

    @Slot()
    def save_proxy_settings(self):
        """Saves the current proxy settings UI state to the config file."""
        # Determine selected type
        proxy_type = "none"
        if self.proxy_system_radio.isChecked():
            proxy_type = "system"
        elif self.proxy_http_radio.isChecked():
            proxy_type = "http"
        elif self.proxy_socks5_radio.isChecked():
            proxy_type = "socks5"

        # Get values from fields
        address = self.proxy_address_input.text().strip()
        port = self.proxy_port_input.text().strip()
        username = self.proxy_user_input.text().strip()
        password = self.proxy_pass_input.text() # Don't strip password

        # Update the config dictionary
        self.config["proxy_config"] = {
            "type": proxy_type,
            "address": address,
            "port": port,
            "username": username,
            "password": password
        }

        # Save the entire config
        save_config(self.config)
        logger.info(f"保存代理设置: 类型={proxy_type}, 地址={address}:{port}")


    @Slot(bool)
    def toggle_proxy_fields(self):
        """Enables/disables manual proxy fields based on radio button selection."""
        # Check which radio button triggered the signal or is currently checked
        is_manual_proxy_enabled = self.proxy_http_radio.isChecked() or self.proxy_socks5_radio.isChecked()

        self.proxy_address_input.setEnabled(is_manual_proxy_enabled)
        self.proxy_port_input.setEnabled(is_manual_proxy_enabled)
        self.proxy_user_input.setEnabled(is_manual_proxy_enabled)
        self.proxy_pass_input.setEnabled(is_manual_proxy_enabled)
        self.proxy_test_button.setEnabled(is_manual_proxy_enabled)

    def get_current_proxy_config(self):
        """
        Constructs the proxy dictionary for requests/aiohttp based on UI settings.
        Returns a tuple: (proxies_dict or None, proxy_type_string)
        """
        proxies = None
        proxy_type = "none"

        if self.proxy_system_radio.isChecked():
            proxy_type = "system"
            # For 'requests', None usually means use system proxies.
            # For 'aiohttp', TrustEnvironment=True in ClientSession handles system proxies.
            # We'll return None here, and the download functions will handle it.
            proxies = None # Indicate system proxies
            logger.info("使用系统代理设置。")
        elif self.proxy_http_radio.isChecked() or self.proxy_socks5_radio.isChecked():
            address = self.proxy_address_input.text().strip()
            port = self.proxy_port_input.text().strip()
            user = self.proxy_user_input.text().strip()
            password = self.proxy_pass_input.text() # Don't strip password

            if not address or not port:
                QMessageBox.warning(self, self.tr("代理配置错误"), self.tr("手动代理需要地址和端口。")) # Wrapped
                return None, "none" # Return None if manual config is incomplete

            # Validate port
            try:
                int(port)
            except ValueError:
                QMessageBox.warning(self, self.tr("代理配置错误"), self.tr("代理端口必须是数字。")) # Wrapped
                return None, "none"

            scheme = ""
            if self.proxy_http_radio.isChecked():
                proxy_type = "http"
                scheme = "http" # requests uses http/https keys, aiohttp uses full URL
            elif self.proxy_socks5_radio.isChecked():
                proxy_type = "socks5"
                scheme = "socks5" # requests uses http/https keys, aiohttp uses full URL

            # Construct proxy URL string (common format)
            auth_part = ""
            if user and password:
                auth_part = f"{user}:{password}@"
            elif user: # Handle username only case if needed, though less common
                # Placeholder comment if needed, or just keep the elif condition
                pass # Or simply remove the lines below if no other logic is needed here

            # --- Construct proxy URL string (common format) ---
            # The lines below were part of the original logic and should remain
            # This section seems unrelated to the misplaced block and should be preserved
            # Ensure the indentation here is correct relative to the outer function
            proxy_full_url = f"{scheme}://{auth_part}{address}:{port}"

            # Format for 'requests' library (dictionary)
            # Format for 'aiohttp' library (string URL passed to 'proxy' argument)
            # We will return the string URL for aiohttp and let download functions adapt if needed
            proxies = proxy_full_url # Return the full URL string for aiohttp
            logger.info(f"使用手动 {proxy_type.upper()} 代理: {scheme}://{address}:{port}")

        elif self.proxy_none_radio.isChecked():
            proxy_type = "none"
            proxies = None
            logger.info("不使用代理。")

        return proxies, proxy_type # Return the constructed proxy info and type

    @Slot()
    def test_proxy_settings_internal(self):
        """Initiates the proxy test in a separate thread."""
        proxies, proxy_type = self.get_current_proxy_config()

        # Only test manual proxies (http or socks5) that have address and port
        if proxy_type not in ["http", "socks5"] or not proxies:
            QMessageBox.information(self, self.tr("代理测试"), self.tr("请先配置并选择 HTTP/HTTPS 或 SOCKS5 手动代理。")) # Wrapped
            return

        # Disable button during test
        self.proxy_test_button.setEnabled(False)
        self.proxy_test_button.setText(self.tr("测试中...")) # Wrapped

        # --- Prepare proxies specifically for the 'requests' library used in the test ---
        # The test worker uses 'requests', which expects a dictionary format.
        requests_proxies = None
        if isinstance(proxies, str): # If get_current_proxy_config returned the URL string
             # Convert the URL string back to the dict format requests expects
             requests_proxies = {
                 "http": proxies,
                 "https": proxies
             }
        elif isinstance(proxies, dict): # If it somehow returned a dict already
             requests_proxies = proxies
        # If proxies is None (e.g., for system or none), requests_proxies remains None

        if not requests_proxies:
             logger.error("无法为代理测试准备 'requests' 库所需的代理字典。")
             QMessageBox.critical(self, self.tr("错误"), self.tr("准备代理测试时出错。")) # Wrapped
             self.proxy_test_button.setEnabled(True)
             self.proxy_test_button.setText(self.tr("测试手动代理")) # Wrapped
             return
        # ---------------------------------------------------------------------------------


        # Run the test in a separate thread using QThreadPool
        # Pass the 'requests' compatible proxy dict
        worker = ProxyTestWorker(requests_proxies)
        worker.signals.finished.connect(self.proxy_test_finished)
        QThreadPool.globalInstance().start(worker)

    @Slot(bool, str)
    def proxy_test_finished(self, success, message):
        """Handles the result of the proxy test."""
        self.proxy_test_button.setEnabled(True)
        self.proxy_test_button.setText(self.tr("测试手动代理")) # Wrapped

        if success:
            QMessageBox.information(self, self.tr("代理测试成功"), f"{self.tr('代理连接成功！')}\n({message})") # Wrapped
        else:
            QMessageBox.warning(self, self.tr("代理测试失败"), f"{self.tr('代理连接失败:')}\n{message}") # Wrapped


# --- Help/About Widget ---
class HelpWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Align content to top

        title_label = QLabel(self.tr("关于 TikTok 批量下载器")) # Wrapped
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        version_label = QLabel(f"{self.tr('版本:')} 1.1 (GUI)") # Wrapped
        layout.addWidget(version_label, alignment=Qt.AlignmentFlag.AlignCenter)

        description_label = QLabel(
            self.tr(
                "本工具旨在帮助用户批量下载 TikTok 视频链接，去除水印。\n"
                "请负责任地使用本工具，并遵守 TikTok 的服务条款和相关版权法律。\n\n"
                "主要功能:\n"
                "- 粘贴或从文件加载多个 TikTok 链接。\n"
                "- 通过可配置的 API 端点获取无水印视频信息。\n"
                "- 支持并发下载以提高效率。\n"
                "- 可选下载封面和标题。\n"
                "- 支持自定义子文件夹保存结构。\n"
                "- 支持 HTTP/SOCKS5 代理。\n"
                "- 提供浅色和深色主题。\n"
                "- 支持多语言界面 (需要翻译文件)。"
            ) # Wrapped long string
        )
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        layout.addSpacing(20)

        api_info_label = QLabel(
             self.tr(
                 "API 配置:\n"
                 "请在“视图”->“API 设置”中配置至少一个有效的第三方 TikTok 解析 API。\n"
                 "程序将按列表顺序尝试 API，直到成功获取信息。\n"
                 "常见的 API 类型可能需要 Key 和 Host (如 RapidAPI)。"
             ) # Wrapped long string
        )
        api_info_label.setWordWrap(True)
        layout.addWidget(api_info_label)

        layout.addSpacing(10)

        proxy_info_label = QLabel(
             self.tr(
                 "代理设置:\n"
                 "如果需要通过代理访问网络，请在“视图”->“代理设置”中配置。\n"
                 "支持系统代理、HTTP/HTTPS 和 SOCKS5 代理。"
             ) # Wrapped long string
        )
        proxy_info_label.setWordWrap(True)
        layout.addWidget(proxy_info_label)

        layout.addSpacing(10)

        folder_template_label = QLabel(
             self.tr(
                 "文件夹模板:\n"
                 "使用“子文件夹模板”可以自定义视频的保存路径。\n"
                 "可用变量: {DATE} (YYYYMMDD), {TIME} (HHMMSS), {AUTHOR_ID} (作者ID), {CUSTOM_TEXT} (自定义文本框内容)。\n"
                 "示例: '{DATE}/{AUTHOR_ID}' 会将视频保存在 '下载路径/20231027/作者ID/' 目录下。"
             ) # Wrapped long string
        )
        folder_template_label.setWordWrap(True)
        layout.addWidget(folder_template_label)


        layout.addStretch() # Push content upwards

        # Initial translation
        self.retranslate_ui()

    def retranslate_ui(self):
        """Retranslates UI elements in the HelpWidget."""
        # Find children by object name or type if needed, or re-set text directly
        # Assuming we can access labels directly for simplicity here
        labels = self.findChildren(QLabel)
        if len(labels) >= 7: # Basic check based on expected number of labels
            labels[0].setText(self.tr("关于 TikTok 批量下载器"))
            labels[1].setText(f"{self.tr('版本:')} 1.1 (GUI)")
            labels[2].setText(
                self.tr(
                    "本工具旨在帮助用户批量下载 TikTok 视频链接，去除水印。\n"
                    "请负责任地使用本工具，并遵守 TikTok 的服务条款和相关版权法律。\n\n"
                    "主要功能:\n"
                    "- 粘贴或从文件加载多个 TikTok 链接。\n"
                    "- 通过可配置的 API 端点获取无水印视频信息。\n"
                    "- 支持并发下载以提高效率。\n"
                    "- 可选下载封面和标题。\n"
                    "- 支持自定义子文件夹保存结构。\n"
                    "- 支持 HTTP/SOCKS5 代理。\n"
                    "- 提供浅色和深色主题。\n"
                    "- 支持多语言界面 (需要翻译文件)。"
                )
            )
            labels[3].setText(
                 self.tr(
                     "API 配置:\n"
                     "请在“视图”->“API 设置”中配置至少一个有效的第三方 TikTok 解析 API。\n"
                     "程序将按列表顺序尝试 API，直到成功获取信息。\n"
                     "常见的 API 类型可能需要 Key 和 Host (如 RapidAPI)。"
                 )
            )
            labels[4].setText(
                 self.tr(
                     "代理设置:\n"
                     "如果需要通过代理访问网络，请在“视图”->“代理设置”中配置。\n"
                     "支持系统代理、HTTP/HTTPS 和 SOCKS5 代理。"
                 )
            )
            labels[5].setText(
                 self.tr(
                     "文件夹模板:\n"
                     "使用“子文件夹模板”可以自定义视频的保存路径。\n"
                     "可用变量: {DATE} (YYYYMMDD), {TIME} (HHMMSS), {AUTHOR_ID} (作者ID), {CUSTOM_TEXT} (自定义文本框内容)。\n"
                     "示例: '{DATE}/{AUTHOR_ID}' 会将视频保存在 '下载路径/20231027/作者ID/' 目录下。"
                 )
            )
        logger.debug("HelpWidget UI retranslated.")


# --- Proxy Test Worker ---
class ProxyTestWorkerSignals(QObject):
    finished = Signal(bool, str) # success (bool), message (str)

class ProxyTestWorker(QRunnable):
    def __init__(self, proxies):
        super().__init__()
        self.proxies = proxies
        self.signals = ProxyTestWorkerSignals()

    @Slot()
    def run(self):
        # Use a common site known to be stable, avoid hitting TikTok API just for testing
        # Google's generate_204 is a good candidate as it returns HTTP 204 No Content
        test_url = "https://www.google.com/generate_204"
        success = False
        message = ""
        headers = { # Use a common browser user-agent
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            import requests # Import requests locally for proxy test
            logger.info(f"Testing proxy: {self.proxies} against {test_url}")
            response = requests.get(test_url,
                                  proxies=self.proxies,
                                  timeout=10, # Increased timeout for proxy test
                                  headers=headers,
                                  allow_redirects=False) # Don't follow redirects for 204 test
            logger.info(f"Proxy test response status: {response.status_code}")
            # Check for 204 No Content specifically, or general 2xx success
            if response.status_code == 204 or 200 <= response.status_code < 300:
                success = True
                message = f"状态码: {response.status_code}"
            else:
                message = f"意外的状态码: {response.status_code}"
        except requests.exceptions.ProxyError as e:
             message = f"代理错误: {e}"
             logger.error(f"Proxy test failed (ProxyError): {e}")
        except requests.exceptions.ConnectTimeout as e:
             message = f"连接超时: {e}"
             logger.error(f"Proxy test failed (ConnectTimeout): {e}")
        except requests.exceptions.ReadTimeout as e:
             message = f"读取超时: {e}"
             logger.error(f"Proxy test failed (ReadTimeout): {e}")
        except requests.exceptions.RequestException as e:
             message = f"请求错误: {e}"
             logger.error(f"Proxy test failed (RequestException): {e}")
        except Exception as e:
             message = f"未知错误: {e}"
             logger.exception("Proxy test failed (Unknown Exception)")

        self.signals.finished.emit(success, message)
# -----------------------


# --- Download Worker Thread ---
class DownloadWorker(QThread):
    add_table_row = Signal(str, int) # url, row_index
    # Signal: row_index, status_text, progress_percent, info_text, title_text, local_cover_path, speed_mbps
    update_progress = Signal(int, str, int, str, str, str, float)
    task_finished = Signal()

    def __init__(self, urls, parent_path, subfolder_template, custom_text, concurrency_limit,
                 proxies=None, api_endpoints=None, # Added api_endpoints
                 download_cover_title=False, cover_title_path=""): # Added cover/title params
        super().__init__()
        self.urls = urls
        self.parent_path = parent_path
        self.subfolder_template = subfolder_template
        self.custom_text = custom_text
        self.concurrency_limit = concurrency_limit
        self.proxies = proxies # Store proxies
        self.api_endpoints = api_endpoints if api_endpoints else [] # Store API endpoints
        self.download_cover_title = download_cover_title
        self.cover_title_path = cover_title_path
        self.is_running = True # Flag to control thread execution
        self.session = None # To hold the shared aiohttp session

    async def process_url(self, original_url, row_index, total_urls, semaphore, session):
        """Processes a single URL: fetches info, downloads video/album."""
        async with semaphore: # Acquire semaphore before processing
            if not self.is_running: # Check if stopped before starting work
                logger.info(f"[Row {row_index}] Stop requested before processing URL.")
                self.update_progress.emit(row_index, "已取消", 0, "用户请求停止", "", "", 0.0)
                return

            logger.info(f"--- [Row {row_index}] Processing URL: {original_url} ---")
            self.update_progress.emit(row_index, "获取信息...", 5, "", "", "", 0.0) # Initial status

            # --- Define variables for template ---
            now = datetime.now()
            date_str = now.strftime("%Y%m%d")
            time_str = now.strftime("%H%M%S")
            author_id_str = "UnknownAuthor" # Default
            # -----------------------------------

            # --- Fetch Info using tiktok_fetcher ---
            # Pass the ordered list of endpoints and proxies
            fetch_success, result_data = await fetch_tiktok_info(
                original_url,
                self.api_endpoints,
                proxies=self.proxies,
                session=session # Pass the shared session
            )
            # -------------------------------------

            if not self.is_running: # Check again after potentially long fetch
                logger.info(f"[Row {row_index}] Stop requested after fetching info.")
                self.update_progress.emit(row_index, "已取消", 0, "用户请求停止", "", "", 0.0)
                return

            if not fetch_success:
                error_msg = result_data or "获取信息失败 (未知错误)"
                logger.error(f"[Row {row_index}] Failed to fetch info for {original_url}: {error_msg}")
                self.update_progress.emit(row_index, "失败 (API)", 0, error_msg, "", "", 0.0) # Error in info, empty title/cover_path
                return # Stop processing this URL

            # --- Process successful fetch result ---
            url_type = result_data.get("type")
            item_title = result_data.get("title", "") # Get title
            author_id = result_data.get("author_id")
            if author_id: author_id_str = sanitize_filename(author_id) # Update for template
            cover_url = result_data.get("cover_url") # Get cover URL
            referer = result_data.get("referer") # Get referer if provided by API

            # --- Update subfolder path with actual author_id ---
            try:
                subfolder_name = self.subfolder_template.format(
                    DATE=date_str,
                    TIME=time_str,
                    AUTHOR_ID=author_id_str,
                    CUSTOM_TEXT=sanitize_filename(self.custom_text) # Sanitize custom text too
                ).replace("/", os.sep).replace("\\", os.sep) # Replace slashes with OS separator
                # Remove potentially problematic leading/trailing separators or spaces
                subfolder_name = subfolder_name.strip(os.sep + " ")
                # Prevent creating folders named just "." or ".." or empty
                if not subfolder_name or subfolder_name in [".", ".."]:
                    logger.warning(f"[Row {row_index}] 无效的子文件夹模板结果 '{subfolder_name}'，将使用默认名称。")
                    subfolder_name = f"{date_str}_{author_id_str}" # Fallback

                save_directory = os.path.join(self.parent_path, subfolder_name)
            except KeyError as e:
                 logger.error(f"[Row {row_index}] 子文件夹模板 '{self.subfolder_template}' 中使用了无效变量: {e}")
                 self.update_progress.emit(row_index, "失败 (模板错误)", 0, f"模板变量错误: {e}", item_title, "", 0.0)
                 return
            except Exception as e: # Catch other potential formatting errors
                 logger.error(f"[Row {row_index}] 创建子文件夹路径时出错: {e}")
                 self.update_progress.emit(row_index, "失败 (路径错误)", 0, f"路径创建错误: {e}", item_title, "", 0.0)
                 return

            # --- Create Save Directory (Async) ---
            try:
                # Use aiofiles.os.makedirs for async directory creation
                await aiofiles.os.makedirs(save_directory, exist_ok=True)
                logger.info(f"  [Row {row_index}] Save directory: {save_directory}")
            except OSError as e:
                logger.error(f"  [Row {row_index}] Failed to create directory {save_directory}: {e}")
                self.update_progress.emit(row_index, "失败 (目录错误)", 0, f"无法创建目录: {e}", item_title, "", 0.0)
                return
            # -----------------------------------

            # --- Handle Cover/Title Download (if enabled) ---
            local_cover_path = ""
            if self.download_cover_title and self.cover_title_path:
                # Create cover/title directory if it doesn't exist (sync is ok here, happens once)
                try:
                    os.makedirs(self.cover_title_path, exist_ok=True)
                except OSError as e:
                    logger.error(f"无法创建封面/标题目录 {self.cover_title_path}: {e}")
                    # Proceed without cover/title download if directory fails
                    self.update_progress.emit(row_index, "处理中 (无封面)", 10, "无法创建封面目录", item_title, "", 0.0) # Update status
                else:
                    # --- Download Cover ---
                    if cover_url:
                        cover_filename_base = sanitize_filename(item_title) or f"tiktok_{author_id_str}_{int(time.time())}"
                        cover_ext = os.path.splitext(cover_url.split('?')[0])[-1] or ".jpg"
                        if len(cover_ext) > 6: cover_ext = ".jpg" # Sanity check extension
                        cover_filename = f"{cover_filename_base}{cover_ext}"
                        local_cover_path = os.path.join(self.cover_title_path, cover_filename)

                        if not os.path.exists(local_cover_path): # Check sync before async download
                            logger.info(f"  [Row {row_index}] Downloading cover to: {local_cover_path}")
                            # Use SYNC download for cover for simplicity within async worker?
                            # Or use download_file_async if preferred
                            cover_success, cover_error = download_file_sync( # Using sync for simplicity
                                cover_url, local_cover_path, referer=referer,
                                row_index=row_index, proxies=self.proxies
                            )
                            if not cover_success:
                                logger.warning(f"  [Row {row_index}] Failed to download cover: {cover_error}")
                                local_cover_path = "" # Reset path if download failed
                            else:
                                # Emit progress update with cover path *after* successful download
                                self.update_progress.emit(row_index, "处理中", 15, "", item_title, local_cover_path, 0.0)
                        else:
                            logger.info(f"  [Row {row_index}] Cover already exists: {local_cover_path}")
                            # Emit progress update with existing cover path
                            self.update_progress.emit(row_index, "处理中", 15, "", item_title, local_cover_path, 0.0)
                    else:
                        logger.warning(f"  [Row {row_index}] No cover URL found in API response.")

                    # --- Save Title ---
                    if item_title:
                        title_filename_base = sanitize_filename(item_title) or f"tiktok_{author_id_str}_{int(time.time())}"
                        title_filename = f"{title_filename_base}.txt"
                        title_save_path = os.path.join(self.cover_title_path, title_filename)
                        if not os.path.exists(title_save_path): # Check sync before async write
                            try:
                                async with aiofiles.open(title_save_path, 'w', encoding='utf-8') as tf:
                                    await tf.write(item_title)
                                logger.info(f"  [Row {row_index}] Title saved to: {title_save_path}")
                            except Exception as e:
                                logger.error(f"  [Row {row_index}] Failed to save title file {title_save_path}: {e}")
                        else:
                             logger.info(f"  [Row {row_index}] Title file already exists: {title_save_path}")
            # ------------------------------------------------

            # --- Download Based on Type ---
            try: # Add try block specifically around download logic
                if url_type == "video":
                    video_url = result_data.get("video_url")
                    if not video_url:
                        logger.error(f"[Row {row_index}] No video URL found in result for {original_url}")
                        self.update_progress.emit(row_index, "失败 (无链接)", 0, "未找到视频链接", item_title, local_cover_path, 0.0)
                        return

                    # --- Determine Filename ---
                    # Use title if available and valid, otherwise fallback
                    base_filename = sanitize_filename(item_title) or f"tiktok_{author_id_str}_{int(time.time())}"
                    # Try to get extension from URL, default to .mp4
                    file_ext = os.path.splitext(video_url.split('?')[0])[-1] or ".mp4"
                    if len(file_ext) > 5: file_ext = ".mp4" # Basic sanity check for extension
                    filename = f"{base_filename}{file_ext}"
                    save_path = os.path.join(save_directory, filename)
                    # ------------------------

                    # Check if file exists (async)
                    if await aiofiles.os.path.exists(save_path):
                        logger.info(f"[Row {row_index}] Video already exists, skipping: {filename}")
                        self.update_progress.emit(row_index, "已跳过 (已存在)", 100, "文件已存在", item_title, local_cover_path, 0.0)
                        return

                    # --- Perform Async Download ---
                    logger.info(f"  [Row {row_index}] Starting async download for: {filename}")
                    # Define progress callback function specific to this download
                    def progress_update_handler(r_idx, downloaded, total, percent, speed):
                        # Ensure signal is emitted only for the correct row
                        if r_idx == row_index and self.is_running: # Check is_running flag
                            self.update_progress.emit(r_idx, "下载中", percent, "", item_title, local_cover_path, speed)

                    # Call the async download function
                    download_success, error_msg = await download_file_async(
                        video_url, save_path, referer=referer,
                        progress_callback=progress_update_handler,
                        row_index=row_index,
                        proxies=self.proxies, # Pass proxies
                        session=session # Pass shared session
                    )
                    # --------------------------

                    if not self.is_running: # Check if stopped during download
                        logger.info(f"[Row {row_index}] Stop requested during video download.")
                        self.update_progress.emit(row_index, "已取消", 0, "用户请求停止", item_title, local_cover_path, 0.0)
                        # Attempt to remove incomplete file
                        if await aiofiles.os.path.exists(save_path):
                            try: await aiofiles.os.remove(save_path); logger.info(f"  [Row {row_index}] Removed incomplete file: {save_path}")
                            except OSError as e: logger.error(f"  [Row {row_index}] Error removing incomplete file {save_path}: {e}")
                        return

                    # --- Final Status Update ---
                    if download_success:
                        final_status = "已完成"
                        final_progress = 100
                        final_info = error_msg or "" # Show warning if size mismatch occurred
                        logger.info(f"[Row {row_index}] Download successful: {filename}")
                    else:
                        final_status = "失败 (下载)"
                        final_progress = 0 # Or keep last known progress? Resetting to 0 for failure.
                        final_info = error_msg or "下载失败 (未知错误)"
                        logger.error(f"[Row {row_index}] Download failed: {filename} - {final_info}")

                    self.update_progress.emit(row_index, final_status, final_progress, final_info, item_title, local_cover_path, 0.0)
                    # -------------------------

                elif url_type == "album":
                    image_urls = result_data.get("image_urls", [])
                    if not image_urls:
                        logger.error(f"[Row {row_index}] No image URLs found in result for album {original_url}")
                        self.update_progress.emit(row_index, "失败 (无链接)", 0, "未找到图片链接", item_title, local_cover_path, 0.0)
                        return

                    # --- Create Album Subdirectory ---
                    # Use title for album folder name, fallback if needed
                    album_folder_name = sanitize_filename(item_title) or f"tiktok_album_{author_id_str}_{int(time.time())}"
                    album_save_dir = os.path.join(save_directory, album_folder_name)
                    try:
                        await aiofiles.os.makedirs(album_save_dir, exist_ok=True)
                        logger.info(f"  [Row {row_index}] Album save directory: {album_save_dir}")
                    except OSError as e:
                        logger.error(f"  [Row {row_index}] Failed to create album directory {album_save_dir}: {e}")
                        self.update_progress.emit(row_index, "失败 (目录错误)", 0, f"无法创建图集目录: {e}", item_title, local_cover_path, 0.0)
                        return
                    # -------------------------------

                    # --- Download Images Sequentially (within the async task) ---
                    logger.info(f"  [Row {row_index}] Starting album download ({len(image_urls)} images) for: {album_folder_name}")
                    self.update_progress.emit(row_index, "下载图集中...", 30, f"0/{len(image_urls)}", item_title, local_cover_path, 0.0) # Initial album status

                    # --- This block was previously misplaced ---
                    all_images_success = True
                    downloaded_count = 0
                    first_img_error = ""
                    # -----------------------------------------

                    # --- Download Images Loop (Re-indented with 4 spaces) ---
                    for idx, img_url in enumerate(image_urls):
                        # Check if stop requested before processing each image
                        if not self.is_running:
                            logger.info(f"[Row {row_index}] Stop requested during album download (image {idx+1}).")
                            first_img_error = "用户请求停止"
                            all_images_success = False
                            break # Exit the image download loop

                        # Calculate approximate progress within the album download phase (30% to 90%)
                        img_progress = 30 + int((idx + 1) / len(image_urls) * 60)
                        # Update progress for the overall album task
                        self.update_progress.emit(row_index, "下载图集中", img_progress, f"{idx+1}/{len(image_urls)}", item_title, local_cover_path, 0.0)

                        # Determine image filename and save path
                        file_ext = os.path.splitext(img_url.split('?')[0])[-1] or ".jpg"
                        if len(file_ext) > 5: file_ext = ".jpg" # Basic sanity check for extension
                        img_filename = f"{idx+1:02d}{file_ext}" # Format as 01.jpg, 02.jpg, etc.
                        img_save_path = os.path.join(album_save_dir, img_filename)

                        # Check if image already exists (async)
                        if await aiofiles.os.path.exists(img_save_path):
                            # logger.info(f"  [Row {row_index}] Image already exists, skipping: {img_filename}") # Less verbose
                            downloaded_count += 1
                            continue # Skip download if exists

                        # Download the image asynchronously
                        # No specific progress callback for individual images
                        img_success, img_error_msg = await download_file_async(
                            img_url, img_save_path, referer=referer,
                            row_index=row_index,
                            proxies=self.proxies, # Pass proxies
                            session=session # Pass shared session
                        )

                        # Handle image download result
                        if not img_success:
                            logger.error(f"  [Row {row_index}] Failed to download image {idx+1}: {img_filename} - {img_error_msg}")
                            all_images_success = False
                            # Store the first image error encountered
                            if not first_img_error:
                                # Try to categorize the error type for a slightly better message
                                if "写入" in (img_error_msg or ""): img_fail_type = "写入"
                                elif "下载" in (img_error_msg or "") or "HTTP" in (img_error_msg or "") or "连接" in (img_error_msg or "") or "超时" in (img_error_msg or ""): img_fail_type = "下载"
                                else: img_fail_type = "处理"
                                first_img_error = f"图片 {idx+1} 失败 ({img_fail_type}): {img_error_msg or '未知错误'}"
                        else:
                            downloaded_count += 1

                        # Small delay between image downloads
                        await asyncio.sleep(DOWNLOAD_DELAY_SECONDS / 2)
                    # --- End of Re-indented Block ---

                    # Determine final status and progress after loop finishes or breaks
                    final_album_status = "图集完成" if all_images_success else "图集部分失败"
                    final_progress = 100 # Show 100% even if partially failed, status indicates failure
                    # Emit final update for the album
                    self.update_progress.emit(row_index, final_album_status, final_progress, first_img_error if not all_images_success else "", item_title, local_cover_path, 0.0)

                else: # Ensure this else aligns with the 'if' and 'elif' above it (Handling unknown type)
                    logger.warning(f"[Row {row_index}] Unknown URL type '{url_type}' returned for {original_url}")
                    self.update_progress.emit(row_index, "失败 (未知类型)", 0, f"无法处理的类型: {url_type}", "", "", 0.0) # Error in info, empty title/cover_path

            except Exception as e: # Ensure alignment with the outer try
                 logger.exception(f"[Row {row_index}] Unexpected error processing URL {original_url}: {e}")
                 self.update_progress.emit(row_index, "失败 (内部错误)", 0, str(e), "", "", 0.0) # Error in info, empty title/cover_path

            # logger.info(f"--- [Row {row_index}] Finished processing ---") # More verbose log if needed
            # Small delay before releasing semaphore and allowing next task
            await asyncio.sleep(REQUEST_DELAY_SECONDS)


    async def run_async(self):
        """Runs the async processing loop with concurrency."""
        logger.info("DownloadWorker run_async method started.")
        total_urls = len(self.urls)
        logger.info(f"Worker thread processing {total_urls} URLs with concurrency limit {self.concurrency_limit}.")

        # Add rows to table first
        logger.info("Adding rows to table...")
        for i, url in enumerate(self.urls):
             self.add_table_row.emit(url, i)
        logger.info("Finished adding rows to table.")

        # --- Create a single aiohttp session for this worker ---
        # Use TrustEnvironment=True to potentially pick up system proxies if manual proxy is not set
        # connector = aiohttp.TCPConnector(ssl=False) if disable_ssl else aiohttp.TCPConnector()
        connector = aiohttp.TCPConnector() # Default connector
        async with aiohttp.ClientSession(connector=connector, headers=COMMON_HEADERS) as session:
            self.session = session # Store session reference if needed for cancellation (though not strictly needed now)
            logger.info("Created shared aiohttp ClientSession for worker.")

            # --- Concurrent processing using Semaphore and gather ---
            semaphore = asyncio.Semaphore(self.concurrency_limit)
            tasks = []
            logger.info("Creating concurrent tasks...")
            for i, url in enumerate(self.urls):
                if not self.is_running: # Check before creating task
                    logger.info(f"Stop requested before creating task for URL {i+1}")
                    break
                logger.info(f"  Creating task for URL {i+1}/{total_urls}: {url}")
                # Create a task for each URL, passing the semaphore AND the session
                task = asyncio.create_task(self.process_url(url, i, total_urls, semaphore, session))
                tasks.append(task)

            if tasks: # Only gather if tasks were created
                logger.info(f"Starting execution of {len(tasks)} tasks...")
                # Wait for all tasks to complete
                await asyncio.gather(*tasks)
                logger.info("Worker thread finished processing all tasks.")
            else:
                logger.info("No tasks were created or executed (likely stopped early).")

        self.session = None # Clear session reference after closing
        logger.info("Closed shared aiohttp ClientSession.")


    def run(self):
        """Entry point for the thread."""
        logger.info("DownloadWorker thread started (run method entry).")
        loop = None
        try:
            # Get or create an event loop for this thread
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Event loop is closed")
            except RuntimeError: # No current event loop or loop is closed
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                logger.info("Created a new asyncio event loop for the worker thread.")

            logger.info("Attempting to run async tasks in the event loop...")
            # Run the main async logic within the loop
            loop.run_until_complete(self.run_async())
            logger.info("Async tasks finished.")

        except Exception as e:
            logger.exception("!!! CRITICAL ERROR in DownloadWorker thread run method !!!")
            try:
                 # Emit critical error with message in info, empty title/cover_path
                 self.update_progress.emit(0, "线程错误", 0, f"严重错误: {e}", "", "", 0.0)
            except Exception as sig_e:
                 logger.error(f"Failed to emit critical error signal: {sig_e}")
        finally:
            # Clean up the loop if we created it
            if loop and not loop.is_running() and not loop.is_closed():
                 # loop.close() # Closing might cause issues if tasks are still pending cleanup
                 logger.info("Event loop cleanup (skipped closing for now).")
            logger.info("DownloadWorker thread run method finishing.")
            self.task_finished.emit()

    def stop(self):
        """Sets the flag to stop the worker thread gracefully."""
        self.is_running = False
        logger.info("Stop requested for worker thread. Setting is_running to False.")
        # Note: Existing running async tasks need to check self.is_running internally.


# --- Main Application Window ---
class DownloaderWindow(QMainWindow): # Inherit from QMainWindow
    def __init__(self, initial_theme="light"): # Accept initial theme
        super().__init__()
        self.worker = None
        self.current_theme = initial_theme # Store current theme
        self.initUI()
        self.create_menus() # Call menu creation
        # Connect signals directly from individual setting widgets
        self.theme_settings_page.theme_changed.connect(self.apply_theme)
        self.language_settings_page.language_changed.connect(self.handle_language_change)
        # Apply initial translations after UI is built but before showing
        self.retranslate_ui() # Added call

    def initUI(self):
        # Use self.tr() for translatable strings
        self.setWindowTitle(self.tr("TikTok 批量下载器")) # Wrapped title
        self.setWindowIcon(QIcon("tiktok.ico")) # Set window icon
        self.setGeometry(100, 100, 800, 700) # Slightly larger height for menu
        self.config = load_config() # Load config early

        # --- Central Widget and Stacked Layout ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        # --- Create Pages ---
        self.download_page = QWidget()
        # Instantiate individual settings pages directly
        self.api_settings_page = ApiSettingsWidget(self)
        self.cover_title_settings_page = CoverTitleSettingsWidget(self)
        self.theme_settings_page = ThemeSettingsWidget(self)
        self.language_settings_page = LanguageSettingsWidget(self)
        self.proxy_settings_page = ProxySettingsWidget(self) # Keep proxy separate
        self.help_page = HelpWidget(self) # Keep help separate

        # Add pages to the stacked widget
        self.stacked_widget.addWidget(self.download_page)
        self.stacked_widget.addWidget(self.api_settings_page)
        self.stacked_widget.addWidget(self.cover_title_settings_page)
        self.stacked_widget.addWidget(self.theme_settings_page)
        self.stacked_widget.addWidget(self.language_settings_page)
        self.stacked_widget.addWidget(self.proxy_settings_page)
        self.stacked_widget.addWidget(self.help_page)

        # --- Build Download Page UI ---
        # We move the original main layout content here
        download_page_layout = QVBoxLayout(self.download_page)
        input_layout = QHBoxLayout()
        settings_form_layout = QFormLayout() # Use QFormLayout for settings
        settings_form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows) # Wrap long labels/widgets
        settings_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        button_layout = QHBoxLayout()

        # --- Input Widgets (on download page) ---
        self.url_input = QTextEdit() # Keep reference for start_download
        self.url_input.setPlaceholderText(self.tr("在此处粘贴 TikTok 链接，每行一个...")) # Wrapped
        input_layout.addWidget(self.url_input, 1) # Give text edit stretch factor

        # --- Input Buttons ---
        input_button_layout = QVBoxLayout()
        self.clear_input_button = QPushButton(self.tr("清空")) # New Clear Button
        self.clear_input_button.setToolTip(self.tr("清空上方输入框中的所有链接")) # Wrapped Tooltip
        self.load_file_button = QPushButton(self.tr("加载文件")) # New Load Button
        self.load_file_button.setToolTip(self.tr("从文本文件加载链接列表 (追加)")) # Wrapped Tooltip
        input_button_layout.addWidget(self.clear_input_button)
        input_button_layout.addWidget(self.load_file_button)
        input_button_layout.addStretch() # Push buttons up
        input_layout.addLayout(input_button_layout) # Add button layout next to text edit
        # -------------------

        # --- Download Settings Widgets (on download page) ---
        # Parent Path
        self.parent_path_label = QLabel(self.tr("父级下载路径:")) # Created Label
        self.parent_path_input = QLineEdit() # Keep reference
        # --- Set path from config or default ---
        loaded_path = self.config.get("download_path")
        if loaded_path and os.path.isdir(loaded_path):
            initial_path = loaded_path
            logger.info(f"从配置加载下载路径: {initial_path}")
        else:
            initial_path = os.path.join(os.path.expanduser("~"), "Downloads", "TikTok_Downloads_Cline")
            if not os.path.exists(initial_path):
                try: os.makedirs(initial_path)
                except OSError: initial_path = os.path.join(os.getcwd(), "downloads")
            logger.info(f"使用默认下载路径: {initial_path}")
        self.parent_path_input.setText(initial_path)
        # ---------------------------------------
        self.browse_button = QPushButton(self.tr("浏览...")) # Wrapped
        parent_path_hbox = QHBoxLayout()
        parent_path_hbox.addWidget(self.parent_path_input, 1)
        parent_path_hbox.addWidget(self.browse_button)
        settings_form_layout.addRow(self.parent_path_label, parent_path_hbox) # Use label var

        # Template Path
        self.template_path_label = QLabel(self.tr("子文件夹模板:")) # Created Label
        self.template_path_input = QLineEdit() # Keep reference
        default_template = "{DATE}_{AUTHOR_ID}"
        self.template_path_input.setText(default_template)
        self.template_path_input.setPlaceholderText(self.tr("例如: {DATE}/{AUTHOR_ID}")) # Wrapped
        # Add description label below the input using a QVBoxLayout within the form row
        template_vbox = QVBoxLayout()
        template_vbox.addWidget(self.template_path_input)
        self.variables_label = QLabel(self.tr("可用: {DATE}, {TIME}, {AUTHOR_ID}, {CUSTOM_TEXT}")) # Wrapped, created var
        self.variables_label.setStyleSheet("font-size: 8pt; color: grey;")
        template_vbox.addWidget(self.variables_label)
        template_vbox.setContentsMargins(0,0,0,0)
        settings_form_layout.addRow(self.template_path_label, template_vbox) # Use label var

        # Custom Text
        self.custom_text_label = QLabel(self.tr("自定义文本:")) # Created Label
        self.custom_text_input = QLineEdit() # Keep reference
        self.custom_text_input.setPlaceholderText(self.tr("用于 {CUSTOM_TEXT} 变量")) # Wrapped
        settings_form_layout.addRow(self.custom_text_label, self.custom_text_input) # Use label var

        # Concurrency Setting
        self.concurrency_label = QLabel(self.tr("并发下载数:")) # Created Label
        self.concurrency_spinbox = QSpinBox() # Keep reference
        self.concurrency_spinbox.setRange(1, 20)
        self.concurrency_spinbox.setValue(DEFAULT_CONCURRENCY)
        self.concurrency_spinbox.setToolTip(self.tr("同时下载的任务数量 (建议 3-5)")) # Wrapped
        settings_form_layout.addRow(self.concurrency_label, self.concurrency_spinbox) # Use label var

        # --- Status Table (on download page) ---
        self.status_label = QLabel(self.tr("下载状态:")) # Created var, Wrapped
        self.status_table = QTableWidget() # Keep reference
        self.status_table.setColumnCount(5) # Increased column count
        # Store header labels for retranslation
        self.status_table_headers = [self.tr("链接"), self.tr("封面"), self.tr("状态"), self.tr("进度"), self.tr("信息/标题")]
        self.status_table.setHorizontalHeaderLabels(self.status_table_headers) # Wrapped
        header = self.status_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # Link
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Cover
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Status
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Progress
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) # Info/Title
        self.status_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.status_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows) # Select whole rows
        self.status_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection) # Allow single row selection
        self.status_table.verticalHeader().setVisible(False) # Hide row numbers

        # Connect double-click signal
        self.status_table.cellDoubleClicked.connect(self.handle_table_double_click)

        # --- Buttons (on download page) ---
        self.start_button = QPushButton(self.tr("开始下载")) # Wrapped
        self.stop_button = QPushButton(self.tr("停止下载")) # New Stop Button
        self.stop_button.setEnabled(False) # Initially disabled
        # TODO: Add Stop button later - Implemented now
        button_layout.addStretch()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button) # Add stop button
        button_layout.addStretch()

        # --- Assemble Download Page Layout ---
        download_page_layout.addLayout(input_layout, 1) # URL input stretch
        download_page_layout.addLayout(settings_form_layout) # Download settings form

        # --- Proxy Settings Group is now MOVED to ProxySettingsWidget ---

        download_page_layout.addWidget(self.status_label) # Use var
        download_page_layout.addWidget(self.status_table, 2) # Status table stretch

        # --- Add Clear Table Button Below Table ---
        self.clear_table_button = QPushButton(self.tr("清空列表")) # New Clear Table Button
        self.clear_table_button.setToolTip(self.tr("清空下方的下载状态列表")) # Wrapped Tooltip
        clear_table_layout = QHBoxLayout()
        clear_table_layout.addStretch()
        clear_table_layout.addWidget(self.clear_table_button)
        clear_table_layout.addStretch()
        download_page_layout.addLayout(clear_table_layout) # Add below table
        # -----------------------------------------

        download_page_layout.addLayout(button_layout) # Start/Stop Buttons at bottom

        # --- Connect Signals (specific to download page widgets) ---
        self.browse_button.clicked.connect(self.browse_folder)
        self.start_button.clicked.connect(self.start_download)
        self.stop_button.clicked.connect(self.stop_download) # Connect stop button
        self.clear_input_button.clicked.connect(self.clear_url_input) # Connect clear button
        self.load_file_button.clicked.connect(self.load_urls_from_file) # Connect load button
        self.clear_table_button.clicked.connect(self.clear_status_table) # Connect clear table button

        logger.info("GUI initialized.")

    # --- Theme Application ---
    @Slot(str)
    def apply_theme(self, theme_name):
        """Applies the specified theme QSS to the application."""
        if theme_name == "dark":
            qss = DARK_THEME_QSS
            self.current_theme = "dark"
        else: # Default to light
            qss = LIGHT_THEME_QSS
            self.current_theme = "light"

        app = QApplication.instance()
        if app:
            app.setStyleSheet(qss)
            logger.info(f"已应用主题: {theme_name}")
            # You might need to force a repaint or style update on some widgets
            # self.update() # Force repaint of the main window
            # QApplication.processEvents() # Process events to ensure update
        else:
            logger.error("无法获取 QApplication 实例来应用主题！")

    # --- Language Change Handling ---
    @Slot()
    def handle_language_change(self):
        """Shows a message box indicating restart is needed for language change."""
        QMessageBox.information(self,
                                self.tr("语言设置"), # Wrapped title
                                self.tr("界面语言设置已保存。\n请重新启动应用程序以应用更改。")) # Wrapped message

    # --- Menu Creation ---
    def create_menus(self):
        # Store menu references for retranslation
        self.menu_bar = self.menuBar()

        # File Menu (Example)
        self.file_menu = self.menu_bar.addMenu(self.tr("&文件")) # Wrapped
        self.exit_action = QAction(QIcon.fromTheme("application-exit"), self.tr("退出"), self) # Wrapped
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.setStatusTip(self.tr("退出应用程序")) # Wrapped
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)

        # --- View Menu (New) ---
        self.view_menu = self.menu_bar.addMenu(self.tr("&视图")) # New View Menu

        self.view_download_action = QAction(self.tr("下载界面"), self) # Action to view download page
        self.view_download_action.setStatusTip(self.tr("切换到主下载界面"))
        self.view_download_action.triggered.connect(lambda: self.stacked_widget.setCurrentWidget(self.download_page))
        self.view_menu.addAction(self.view_download_action)


        # --- Settings Menu ---
        self.settings_menu = self.menu_bar.addMenu(self.tr("&设置")) # Wrapped

        # Actions directly under Settings
        self.api_settings_action = QAction(self.tr("API 设置"), self)
        self.api_settings_action.setStatusTip(self.tr("切换到 API 设置界面"))
        # Point to the specific API settings page
        self.api_settings_action.triggered.connect(lambda: self.stacked_widget.setCurrentWidget(self.api_settings_page))
        self.settings_menu.addAction(self.api_settings_action)

        self.proxy_settings_action = QAction(self.tr("代理设置"), self)
        self.proxy_settings_action.setStatusTip(self.tr("切换到代理设置界面"))
        # Proxy page remains separate
        self.proxy_settings_action.triggered.connect(lambda: self.stacked_widget.setCurrentWidget(self.proxy_settings_page))
        self.settings_menu.addAction(self.proxy_settings_action)

        # Cover/Title settings now point to its own page
        self.cover_title_settings_action = QAction(self.tr("封面与标题设置"), self)
        self.cover_title_settings_action.setStatusTip(self.tr("切换到封面与标题设置界面"))
        # Point to the specific Cover/Title settings page
        self.cover_title_settings_action.triggered.connect(lambda: self.stacked_widget.setCurrentWidget(self.cover_title_settings_page))
        self.settings_menu.addAction(self.cover_title_settings_action)

        self.settings_menu.addSeparator()

        # Preferences Submenu
        self.preferences_menu = self.settings_menu.addMenu(self.tr("偏好设置")) # Wrapped

        # Actions under Preferences now point to their specific pages
        self.theme_settings_action = QAction(self.tr("主题设置"), self) # Wrapped
        self.theme_settings_action.setStatusTip(self.tr("切换到主题设置界面")) # Wrapped
        # Point to the specific Theme settings page
        self.theme_settings_action.triggered.connect(lambda: self.stacked_widget.setCurrentWidget(self.theme_settings_page))
        self.preferences_menu.addAction(self.theme_settings_action)

        self.language_settings_action = QAction(self.tr("语言设置"), self) # Wrapped
        self.language_settings_action.setStatusTip(self.tr("切换到语言设置界面")) # Wrapped
        # Point to the specific Language settings page
        self.language_settings_action.triggered.connect(lambda: self.stacked_widget.setCurrentWidget(self.language_settings_page))
        self.preferences_menu.addAction(self.language_settings_action)


        # --- Help Menu ---
        self.help_menu = self.menu_bar.addMenu(self.tr("&帮助")) # Wrapped
        self.about_action = QAction(self.tr("关于"), self) # Wrapped
        self.about_action.setStatusTip(self.tr("显示关于信息")) # Added status tip
        self.about_action.triggered.connect(lambda: self.stacked_widget.setCurrentWidget(self.help_page))
        self.help_menu.addAction(self.about_action)

    # --- I18N Retranslation ---
    def retranslate_ui(self):
        """Retranslates UI elements marked with self.tr()"""
        # Retranslate Window Title
        self.setWindowTitle(self.tr("TikTok 批量下载器"))

        # Retranslate Download Page Elements
        self.url_input.setPlaceholderText(self.tr("在此处粘贴 TikTok 链接，每行一个..."))
        self.parent_path_label.setText(self.tr("父级下载路径:"))
        self.browse_button.setText(self.tr("浏览..."))
        self.template_path_label.setText(self.tr("子文件夹模板:"))
        self.template_path_input.setPlaceholderText(self.tr("例如: {DATE}/{AUTHOR_ID}"))
        self.variables_label.setText(self.tr("可用: {DATE}, {TIME}, {AUTHOR_ID}, {CUSTOM_TEXT}"))
        self.custom_text_label.setText(self.tr("自定义文本:"))
        self.custom_text_input.setPlaceholderText(self.tr("用于 {CUSTOM_TEXT} 变量"))
        self.concurrency_label.setText(self.tr("并发下载数:"))
        self.concurrency_spinbox.setToolTip(self.tr("同时下载的任务数量 (建议 3-5)"))
        self.status_label.setText(self.tr("下载状态:"))
        self.clear_input_button.setText(self.tr("清空")) # Retranslate clear button
        self.clear_input_button.setToolTip(self.tr("清空上方输入框中的所有链接"))
        self.load_file_button.setText(self.tr("加载文件")) # Retranslate load button
        self.load_file_button.setToolTip(self.tr("从文本文件加载链接列表 (追加)"))
        self.clear_table_button.setText(self.tr("清空列表")) # Retranslate clear table button
        self.clear_table_button.setToolTip(self.tr("清空下方的下载状态列表"))
        self.start_button.setText(self.tr("开始下载"))
        self.stop_button.setText(self.tr("停止下载")) # Retranslate stop button

        # Retranslate Table Headers
        self.status_table_headers = [self.tr("链接"), self.tr("封面"), self.tr("状态"), self.tr("进度"), self.tr("信息/标题")]
        self.status_table.setHorizontalHeaderLabels(self.status_table_headers)

        # Retranslate Menus and Actions
        self.file_menu.setTitle(self.tr("&文件"))
        self.exit_action.setText(self.tr("退出"))
        self.exit_action.setStatusTip(self.tr("退出应用程序"))

        # Retranslate View Menu (Simplified - Only Download Interface)
        self.view_menu.setTitle(self.tr("&视图"))
        self.view_download_action.setText(self.tr("下载界面"))
        self.view_download_action.setStatusTip(self.tr("切换到主下载界面"))


        # Retranslate Settings Menu
        self.settings_menu.setTitle(self.tr("&设置"))
        self.api_settings_action.setText(self.tr("API 设置"))
        self.api_settings_action.setStatusTip(self.tr("切换到 API 设置界面"))
        self.proxy_settings_action.setText(self.tr("代理设置"))
        self.proxy_settings_action.setStatusTip(self.tr("切换到代理设置界面"))
        self.cover_title_settings_action.setText(self.tr("封面与标题设置"))
        self.cover_title_settings_action.setStatusTip(self.tr("切换到封面与标题设置界面"))

        # Retranslate Preferences Submenu
        self.preferences_menu.setTitle(self.tr("偏好设置"))
        self.theme_settings_action.setText(self.tr("主题设置"))
        self.theme_settings_action.setStatusTip(self.tr("切换到主题设置界面"))
        self.language_settings_action.setText(self.tr("语言设置"))
        self.language_settings_action.setStatusTip(self.tr("切换到语言设置界面"))

        # Retranslate Help Menu
        self.help_menu.setTitle(self.tr("&帮助"))
        self.about_action.setText(self.tr("关于"))
        self.about_action.setStatusTip(self.tr("显示关于信息"))

        # Retranslate individual child setting widgets
        if hasattr(self, 'api_settings_page') and self.api_settings_page:
            self.api_settings_page.retranslate_ui()
        if hasattr(self, 'cover_title_settings_page') and self.cover_title_settings_page:
            self.cover_title_settings_page.retranslate_ui()
        if hasattr(self, 'theme_settings_page') and self.theme_settings_page:
            self.theme_settings_page.retranslate_ui()
        if hasattr(self, 'language_settings_page') and self.language_settings_page:
            self.language_settings_page.retranslate_ui()
        # Retranslate other pages
        if hasattr(self, 'proxy_settings_page') and self.proxy_settings_page:
            self.proxy_settings_page.retranslate_ui()
        if hasattr(self, 'help_page') and self.help_page:
            self.help_page.retranslate_ui()

        # Update status bar message (example)
            self.statusBar().showMessage(self.tr("准备就绪"), 3000) # Show "Ready" for 3 seconds

        logger.info("UI retranslated.")

    # --- Table Double-Click Handler ---
    @Slot(int, int)
    def handle_table_double_click(self, row, column):
        """Handles double-clicking on a cell, specifically to open the cover image."""
        # Column indices: 0:Link, 1:Cover, 2:Status, 3:Progress, 4:Info/Title
        if column == 1: # Check if the double-clicked column is the 'Cover' column
            cover_widget = self.status_table.cellWidget(row, column)
            if isinstance(cover_widget, QLabel):
                tooltip = cover_widget.toolTip()
                # Extract path from tooltip (assuming format "...\n路径: C:\path\to\image.jpg")
                path_prefix = self.tr("路径:") # Use translated prefix
                if path_prefix in tooltip:
                    try:
                        image_path = tooltip.split(path_prefix)[1].strip()
                        if os.path.exists(image_path):
                            logger.info(f"尝试打开封面图片: {image_path}")
                            try:
                                # Use os.startfile on Windows (more reliable for various file types)
                                os.startfile(image_path)
                            except AttributeError: # Fallback for non-Windows or if startfile fails
                                import subprocess, platform
                                if platform.system() == 'Darwin':       # macOS
                                    subprocess.call(('open', image_path))
                                elif platform.system() == 'Linux':    # Linux
                                    subprocess.call(('xdg-open', image_path))
                                else: # Fallback or other OS - might not work
                                     logger.warning("无法确定用于打开文件的命令。")
                                     QMessageBox.information(self, self.tr("无法打开"), self.tr("无法自动打开文件。请手动导航到:\n{0}").format(image_path)) # Wrapped
                            except Exception as e:
                                logger.error(f"打开文件时出错 {image_path}: {e}")
                                QMessageBox.warning(self, self.tr("错误"), f"{self.tr('打开文件时出错:')}\n{e}") # Wrapped
                        else:
                            logger.warning(f"封面路径不存在: {image_path}")
                            QMessageBox.warning(self, self.tr("文件未找到"), self.tr("封面图片文件未找到:\n{0}").format(image_path)) # Wrapped
                    except Exception as e:
                        logger.error(f"解析封面路径或打开文件时出错: {e}")
            else:
                logger.debug(f"在行 {row}, 列 {column} 双击，但不是封面单元格或无有效标签。")


    # --- Proxy Settings Logic (Now delegates to ProxySettingsWidget) ---
    def get_proxy_settings(self):
        """Gets proxy settings from the dedicated proxy settings page."""
        if self.proxy_settings_page:
            return self.proxy_settings_page.get_current_proxy_config()
        else:
            logger.error("Proxy settings page not initialized!")
            return None, "none"

    # Note: The test_proxy_settings logic is now fully contained within ProxySettingsWidget
    # We don't need a separate method here in the main window anymore.

    # --- Other Slots ---
    @Slot()
    def clear_status_table(self):
        """Clears all rows from the status table."""
        self.status_table.setRowCount(0)
        logger.info("Status table cleared.")
        self.statusBar().showMessage(self.tr("状态列表已清空"), 2000) # Wrapped

    @Slot()
    def clear_url_input(self):
        """Clears the URL input text edit."""
        self.url_input.clear()
        logger.info("URL input cleared.")
        self.statusBar().showMessage(self.tr("输入框已清空"), 2000) # Wrapped

    @Slot()
    def start_download(self):
        """Starts the download process in a separate thread."""
        urls_text = self.url_input.toPlainText().strip()
        if not urls_text:
            QMessageBox.warning(self, self.tr("无链接"), self.tr("请输入或加载至少一个 TikTok 链接。")) # Wrapped
            return

        urls = [url.strip() for url in urls_text.splitlines() if url.strip()]
        if not urls:
            QMessageBox.warning(self, self.tr("无链接"), self.tr("未找到有效的 TikTok 链接。")) # Wrapped
            return

        # --- Get Settings ---
        parent_path = self.parent_path_input.text().strip()
        if not parent_path or not os.path.isdir(parent_path):
            QMessageBox.warning(self, self.tr("路径无效"), self.tr("请选择一个有效的父级下载路径。")) # Wrapped
            return

        subfolder_template = self.template_path_input.text().strip()
        custom_text = self.custom_text_input.text().strip()
        concurrency_limit = self.concurrency_spinbox.value()

        # --- Get API and Proxy Settings ---
        # Get API settings from the dedicated API page
        api_endpoints = self.api_settings_page.get_api_endpoints()
        active_api = self.api_settings_page.get_active_api_endpoint()
        if not api_endpoints:
             QMessageBox.warning(self, self.tr("API 未配置"), self.tr("请先在“设置”->“API 设置”中添加并激活至少一个 API 端点。")) # Wrapped (Updated menu path)
             return
        if not active_api:
             QMessageBox.warning(self, self.tr("无活动 API"), self.tr("请在“设置”->“API 设置”中选择一个活动 API 端点。")) # Wrapped (Updated menu path)
             return
        # Order endpoints with active one first
        ordered_endpoints = [active_api] + [ep for ep in api_endpoints if ep != active_api]

        proxies, _ = self.get_proxy_settings() # Get proxy dict/string

        # --- Get Cover/Title Settings ---
        # Get Cover/Title settings from the dedicated Cover/Title page
        download_cover_title = self.cover_title_settings_page.is_cover_title_download_enabled()
        cover_title_path = self.cover_title_settings_page.get_cover_title_path()
        if download_cover_title and (not cover_title_path or not os.path.isdir(cover_title_path)):
             # Use self.tr() for QMessageBox text
             reply = QMessageBox.warning(self, self.tr("封面路径无效"), # Wrapped
                                         self.tr("已启用封面/标题下载，但未指定有效的保存路径。\n是否继续下载而不保存封面/标题？"), # Wrapped
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
             if reply == QMessageBox.StandardButton.No:
                 return # User chose not to proceed
             else:
                 download_cover_title = False # Disable cover download for this run
                 logger.warning("封面/标题路径无效，本次下载将禁用封面/标题保存。")


        # --- Clear Table and Start Worker ---
        self.status_table.setRowCount(0) # Clear previous results
        logger.info(f"开始下载 {len(urls)} 个链接...")
        self.statusBar().showMessage(self.tr("开始下载..."), 0) # Persistent message

        # Disable start button, enable stop button
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.url_input.setReadOnly(True) # Make input read-only during download

        # Create and start the worker thread
        self.worker = DownloadWorker(
            urls, parent_path, subfolder_template, custom_text, concurrency_limit,
            proxies=proxies, # Pass proxies
            api_endpoints=ordered_endpoints, # Pass ordered API list
            download_cover_title=download_cover_title, # Pass cover setting
            cover_title_path=cover_title_path # Pass cover path
        )
        self.worker.add_table_row.connect(self.add_table_row_slot)
        self.worker.update_progress.connect(self.update_progress_slot)
        self.worker.task_finished.connect(self.download_finished)
        self.worker.start()

    @Slot()
    def stop_download(self):
        """Requests the worker thread to stop."""
        if self.worker and self.worker.isRunning():
            logger.info("用户请求停止下载...")
            self.statusBar().showMessage(self.tr("正在停止..."), 0) # Persistent message
            self.worker.stop() # Signal the worker to stop
            # Keep stop button enabled until worker confirms finish
            # self.stop_button.setEnabled(False) # Disable stop button immediately? No, wait for finish.
        else:
            logger.info("没有活动的下载任务可以停止。")

    @Slot()
    def download_finished(self):
        """Called when the worker thread finishes."""
        logger.info("下载任务已完成或停止。")
        self.statusBar().showMessage(self.tr("下载完成"), 5000) # Show "Download Complete" for 5 seconds
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.url_input.setReadOnly(False) # Make input editable again
        self.worker = None # Clear worker reference

    @Slot()
    def load_urls_from_file(self):
        """Loads URLs from a text file and appends them to the input."""
        # Use self.tr() for dialog title and filter
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("加载链接文件"), # Wrapped title
            os.path.expanduser("~"), # Start in home directory
            self.tr("文本文件 (*.txt);;所有文件 (*)") # Wrapped filter
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    urls_from_file = f.read().strip()
                if urls_from_file:
                    current_text = self.url_input.toPlainText().strip()
                    # Add a newline if current text is not empty
                    separator = "\n" if current_text else ""
                    self.url_input.setPlainText(current_text + separator + urls_from_file)
                    logger.info(f"从文件 '{file_path}' 加载了链接。")
                    # Use self.tr() for status message
                    self.statusBar().showMessage(self.tr("已从文件加载链接"), 3000) # Wrapped
                else:
                    logger.warning(f"文件 '{file_path}' 为空。")
                    # Use self.tr() for status message
                    self.statusBar().showMessage(self.tr("选择的文件为空"), 3000) # Wrapped
            except Exception as e:
                logger.error(f"加载文件 '{file_path}' 时出错: {e}")
                # Use self.tr() for QMessageBox
                QMessageBox.critical(self, self.tr("错误"), f"{self.tr('加载文件时出错:')}\n{e}") # Wrapped

    @Slot()
    def browse_folder(self):
        start_dir = self.parent_path_input.text()
        if not os.path.isdir(start_dir): start_dir = os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(self, "选择父级下载文件夹", start_dir)
        if directory:
            self.parent_path_input.setText(directory)
            logger.info(f"Parent download path set to: {directory}")
            # --- Save selected path to config ---
            self.config["download_path"] = directory
            save_config(self.config)
            # ------------------------------------

    @Slot(str, int)
    def add_table_row_slot(self, url, row_index):
        self.status_table.insertRow(row_index)
        url_item = QTableWidgetItem(url)
        # Initial status doesn't need queue number with concurrency
        status_item = QTableWidgetItem("待处理")
        # progress_item = QTableWidgetItem("0%") # Replaced by progress bar
        info_item = QTableWidgetItem("") # Info/Title column
        status_item.setForeground(QColor('grey'))

        # --- Create and add Progress Bar ---
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setTextVisible(True) # Show percentage text on bar
        progress_bar.setFormat("%p%") # Show percentage format
        # Apply Windows-like green stylesheet
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid grey;
                border-radius: 3px; /* Slightly less rounded */
                text-align: center;
                background-color: #E0E0E0; /* Lighter grey background */
                height: 18px; /* Explicit height */
            }
            QProgressBar::chunk {
                background-color: #4CAF50; /* Solid Green */
                border-radius: 3px; /* Match parent */
                margin: 1px; /* Small margin for visual separation */
            }
        """)
        # ---------------------------------

        # Column indices: 0:Link, 1:Cover, 2:Status, 3:Progress, 4:Info/Title
        self.status_table.setItem(row_index, 0, url_item)
        # Cover cell (column 1) will be populated later by update_progress_slot
        self.status_table.setItem(row_index, 2, status_item)
        self.status_table.setCellWidget(row_index, 3, progress_bar) # Progress bar in column 3
        self.status_table.setItem(row_index, 4, info_item) # Info/Title in column 4
        self.status_table.resizeRowToContents(row_index) # Adjust row height

    @Slot(int, str, int, str, str, str, float) # Added local_cover_path parameter
    def update_progress_slot(self, row_index, status_text, progress_percent, info_text, title_text, local_cover_path, speed_mbps):
        if 0 <= row_index < self.status_table.rowCount():
            # Column indices: 0:Link, 1:Cover, 2:Status, 3:Progress, 4:Info/Title
            status_item = self.status_table.item(row_index, 2)
            progress_bar = self.status_table.cellWidget(row_index, 3) # Get the progress bar widget
            info_item = self.status_table.item(row_index, 4) # Info/Title item

            if not status_item: logger.error(f"Status item missing for row {row_index}"); return
            if not isinstance(progress_bar, QProgressBar): logger.error(f"Progress bar widget missing or wrong type for row {row_index}"); return
            if not info_item: logger.error(f"Info item missing for row {row_index}"); return

            # Update Status Text (Append Speed if downloading)
            current_status_text = status_text
            if "下载中" in status_text and speed_mbps > 0:
                current_status_text = f"{status_text} ({speed_mbps:.2f} MB/s)"
            status_item.setText(current_status_text)

            # Update Progress Bar Value
            progress_bar.setValue(progress_percent)

            # Update Info/Title Text and Tooltips - Prioritize info_text (errors), then title_text
            display_text = info_text or title_text # Show error/warning if present, otherwise title
            tooltip_text = display_text # Tooltip shows the same for info column
            info_item.setText(display_text)
            info_item.setToolTip(tooltip_text) # Set tooltip for info column

            # Update Cover Cell (Column 1)
            cover_label = self.status_table.cellWidget(row_index, 1) # Check if label exists
            # Check cover download setting from the dedicated page
            if self.cover_title_settings_page.is_cover_title_download_enabled() and local_cover_path and os.path.exists(local_cover_path):
                if not isinstance(cover_label, QLabel): # Create label if it doesn't exist
                    cover_label = QLabel()
                    cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.status_table.setCellWidget(row_index, 1, cover_label)
                    # Set fixed size for cover cell/label?
                    self.status_table.setColumnWidth(1, 80) # Example fixed width
                    self.status_table.setRowHeight(row_index, 60) # Example fixed height

                pixmap = QPixmap(local_cover_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(70, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    cover_label.setPixmap(scaled_pixmap)
                    cover_label.setToolTip(f"双击放大\n路径: {local_cover_path}") # Add path to tooltip
                else:
                    cover_label.setText("无法加载")
                    cover_label.setToolTip(f"无法加载封面:\n{local_cover_path}")
            elif isinstance(cover_label, QLabel): # Clear existing label if cover not available/disabled
                 cover_label.clear()
                 cover_label.setToolTip("")


            # Update Status Icon and Tooltip
            status_item.setIcon(QIcon()) # Reset icon first
            status_item.setToolTip("") # Reset tooltip first

            # Define colors
            color_green = "#4CAF50"
            color_red = "#F44336"
            color_orange = "#FF9800"
            color_grey = "#E0E0E0" # Background color
    # ---------------------------------------

# --- Main Execution Block ---
if __name__ == "__main__":
    try: # Add try block
        # --- Create Application Instance ---
        app = QApplication(sys.argv) # Ensure app instance is created first

        # --- Load Config ---
        config = load_config() # Indent this line

        # --- Load and Install Translator --- # Indent this block
        translator = QTranslator()
        qt_translator = QTranslator() # For Qt standard translations

        preferred_language = config.get("preferred_language", "zh_CN") # Default to zh_CN
        logger.info(f"检测到首选语言: {preferred_language}")

        # Construct path to translation files (assuming they are in 'translations' subdir)
        translation_path = "translations"
        # Try loading app-specific translation first
        app_translation_loaded = False
        if preferred_language != "zh_CN": # Don't load for source language
            # Try loading assistant translation (adjust filename if needed)
            app_translation_file = os.path.join(translation_path, f"assistant_{preferred_language}.qm")
            if os.path.exists(app_translation_file):
                if translator.load(app_translation_file):
                    app.installTranslator(translator)
                    logger.info(f"成功加载并安装应用翻译文件: {app_translation_file}")
                    app_translation_loaded = True
                else:
                    logger.error(f"加载应用翻译文件失败: {app_translation_file}")
            else:
                logger.warning(f"应用翻译文件未找到: {app_translation_file}")

        # Load Qt standard translations (important for built-in dialogs like file picker)
        # Use QLibraryInfo to find the standard translations path
        qt_translation_file = QLibraryInfo.location(QLibraryInfo.LibraryPath.TranslationsPath)
        if preferred_language != "en": # Qt base translations are often based on English source
            if qt_translator.load(QLocale(preferred_language), "qtbase", "_", qt_translation_file):
                app.installTranslator(qt_translator)
                logger.info(f"成功加载并安装 Qt 标准翻译 (qtbase_{preferred_language}.qm)")
            else:
                logger.warning(f"加载 Qt 标准翻译文件失败 (qtbase_{preferred_language}.qm) at {qt_translation_file}")

        # --- Apply Initial Theme ---
        initial_theme = config.get("theme", DEFAULT_THEME)
        initial_qss = DARK_THEME_QSS if initial_theme == "dark" else LIGHT_THEME_QSS
        app.setStyleSheet(initial_qss)
        logger.info(f"应用初始主题: {initial_theme}")
        # -----------------------------------------

        # Pass initial theme to window
        window = DownloaderWindow(initial_theme=initial_theme)
        window.show()

        exit_code = app.exec() # Store exit code
        sys.exit(exit_code)

    except Exception as e: # Catch any exception during initialization or execution
        logger.exception("!!! GUI 主程序块发生严重错误 !!!")
        # Optionally display a simple error message box if possible
        try:
            # Attempt to show a basic message box even during early errors
            error_app = QApplication.instance() # Get existing instance or create minimal one
            if not error_app:
                 error_app = QApplication([]) # Minimal instance if none exists
            QMessageBox.critical(None, "严重错误", f"应用程序遇到严重错误并将关闭。\n\n错误:\n{e}\n\n请查看控制台日志获取详细信息。")
        except Exception as msg_e:
            logger.error(f"显示严重错误消息框时出错: {msg_e}")
        # Ensure exit code reflects error
        sys.exit(1)

    finally: # Add finally block
        # This will execute whether the app exits normally or crashes
        print("\n--- 应用程序执行结束 ---")
        input("按 Enter 键关闭此窗口...") # Pause the console window
