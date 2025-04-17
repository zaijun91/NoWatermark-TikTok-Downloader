import logging
import time
import asyncio
import httpx
import json # Import json for parsing

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s')

# --- Constants ---
# Common keys to look for in API responses for the NWM video URL
NWM_VIDEO_URL_KEYS = ['hdplay', 'play', 'nwm_video_url', 'video_url', 'download_url', 'url', 'nwmUrl', 'videoUrlNwm']
# Common keys for metadata
METADATA_KEYS = {
    'aweme_id': ['id', 'aweme_id', 'awemeId'],
    'title': ['title', 'desc', 'description'],
    'author_nickname': ['author.nickname', 'author.unique_id', 'author_nickname', 'authorName'],
    'author_id': ['author.id', 'author.unique_id', 'author_id', 'authorId'],
    'create_time': ['create_time', 'createTime'],
    'music_title': ['music.title', 'musicTitle'],
    'cover_url': ['dynamic_cover', 'cover', 'origin_cover', 'coverUrl', 'videoCover'],
    'album_list': ['images', 'imageList', 'album_list'] # Keys for image URLs in albums
}
# -----------------

def _get_nested_value(data_dict, key_path_list):
    """Safely retrieves a value from a nested dictionary using a list of possible key paths."""
    if not isinstance(data_dict, dict):
        return None
    for key_path in key_path_list:
        keys = key_path.split('.')
        current_val = data_dict
        found = True
        for key in keys:
            if isinstance(current_val, dict) and key in current_val:
                current_val = current_val[key]
            else:
                found = False
                break
        if found:
            return current_val
    return None

async def call_external_tiktok_api(api_config, original_url, proxies=None):
    """
    Calls a specific external TikTok download API endpoint using its configuration.

    Args:
        api_config (dict): A dictionary containing the API configuration
                           (name, url, key, host, param_name, method).
        original_url (str): The TikTok video/album URL to analyze.
        proxies (dict, optional): Dictionary of proxies for the HTTP request. Defaults to None.

    Returns:
        dict: A dictionary containing video/album information or an error dictionary.
              Includes 'status': 'success' or 'failed', and 'reason' on failure.
    """
    api_name = api_config.get('name', 'Unnamed API')
    api_url = api_config.get('url')
    api_key = api_config.get('key')
    api_host = api_config.get('host')
    param_name = api_config.get('param_name', 'url') # Default parameter name is 'url'
    method = api_config.get('method', 'GET').upper() # Default method is GET

    if not api_url:
        logging.error(f"API '{api_name}' is missing 'url' in configuration.")
        return {'status': 'failed', 'reason': f"API '{api_name}' 配置缺少 URL", 'original_url': original_url}

    logging.info(f"Calling API '{api_name}' ({method} {api_url}) for TikTok URL: {original_url}")
    start_time = time.time()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    # Add RapidAPI headers if key and host are provided
    if api_key and api_host:
        headers['x-rapidapi-key'] = api_key
        headers['x-rapidapi-host'] = api_host
        logging.debug(f"  Added RapidAPI headers for host: {api_host}")

    params = {}
    data = {} # For POST requests

    # Prepare parameters or data based on method
    if method == 'GET':
        params[param_name] = original_url
        # Optionally add hd=1 if not already part of the base URL or other params
        if 'hd' not in params and 'hd=' not in api_url.lower():
            params['hd'] = '1'
    elif method == 'POST':
        # Assuming POST sends data as JSON body for now
        data = {param_name: original_url}
        if 'hd' not in data and 'hd=' not in api_url.lower():
             data['hd'] = '1'
        headers['Content-Type'] = 'application/json' # Assume JSON post
    else:
        logging.error(f"Unsupported HTTP method '{method}' for API '{api_name}'.")
        return {'status': 'failed', 'reason': f"不支持的 HTTP 方法: {method}", 'original_url': original_url}

    logging.debug(f"  Request Headers: {headers}")
    logging.debug(f"  Request Params (GET): {params}")
    logging.debug(f"  Request Data (POST): {data}")

    response_data = {} # Initialize response_data

    try:
        async with httpx.AsyncClient(proxies=proxies, follow_redirects=True, timeout=60) as client:
            if method == 'GET':
                response = await client.get(api_url, headers=headers, params=params)
            elif method == 'POST':
                response = await client.post(api_url, headers=headers, json=data) # Send data as JSON

            logging.debug(f"API '{api_name}' response status code for {original_url}: {response.status_code}")

            # Check for non-JSON content types first
            content_type = response.headers.get('content-type', '').lower()
            if 'application/json' not in content_type:
                 logging.error(f"API '{api_name}' returned non-JSON content type: {content_type} for {original_url}. Response text: {response.text[:500]}")
                 return {'status': 'failed', 'reason': f"API '{api_name}' 返回非 JSON 内容 ({content_type})", 'original_url': original_url}

            # Attempt to parse JSON, handle potential errors
            try:
                response_data = response.json()
                logging.debug(f"API '{api_name}' response JSON for {original_url}: {json.dumps(response_data, indent=2)}") # Pretty print JSON
            except json.JSONDecodeError as e_json:
                logging.error(f"Failed to decode JSON response from API '{api_name}' for {original_url}. Error: {e_json}. Response text: {response.text[:500]}")
                return {'status': 'failed', 'reason': f"API '{api_name}' 返回无效 JSON", 'original_url': original_url}

            # Raise exception for 4xx or 5xx status codes AFTER attempting to get JSON error message
            response.raise_for_status()

        analyze_time = format((time.time() - start_time), '.4f')

        # --- Process the API response ---
        # APIs might nest the actual data under a 'data' key
        source_dict = response_data.get('data', response_data) # Use top-level dict if 'data' key doesn't exist or isn't a dict
        if not isinstance(source_dict, dict):
             # If even after checking 'data', we don't have a dict, fail
             logging.error(f"Could not find usable dictionary in API '{api_name}' response for {original_url}. Response: {response_data}")
             return {'status': 'failed', 'reason': f"API '{api_name}' 响应格式无法识别", 'original_url': original_url}

        # --- Determine if it's an album or video ---
        # Heuristic: Look for album-specific keys or check a type indicator if provided by API
        album_list = _get_nested_value(source_dict, METADATA_KEYS['album_list'])
        is_album = bool(album_list) and isinstance(album_list, list) and len(album_list) > 0
        url_type = 'album' if is_album else 'video'
        logging.info(f"Determined type based on API '{api_name}' response: {url_type}")

        # --- Extract common metadata ---
        aweme_id = _get_nested_value(source_dict, METADATA_KEYS['aweme_id'])
        title = _get_nested_value(source_dict, METADATA_KEYS['title'])
        author_nickname = _get_nested_value(source_dict, METADATA_KEYS['author_nickname'])
        author_id = _get_nested_value(source_dict, METADATA_KEYS['author_id'])
        create_time = _get_nested_value(source_dict, METADATA_KEYS['create_time'])
        music_title = _get_nested_value(source_dict, METADATA_KEYS['music_title'])
        cover_url = _get_nested_value(source_dict, METADATA_KEYS['cover_url'])

        result_data = {
            'status': 'success',
            'analyze_time': f"{analyze_time}s (API: {api_name})", # Include API name in time
            'url_type': url_type,
            'platform': 'tiktok',
            'original_url': original_url,
            'cover_url': cover_url, # Common cover URL
        }

        if is_album:
            # Ensure album_list contains valid URLs (sometimes APIs return objects)
            valid_album_urls = []
            if isinstance(album_list, list):
                for item in album_list:
                    if isinstance(item, str) and item.startswith('http'):
                        valid_album_urls.append(item)
                    elif isinstance(item, dict): # Handle cases where images are dicts with a URL key
                        img_url = _get_nested_value(item, ['url', 'imageURL', 'src']) # Common keys for URL within image object
                        if isinstance(img_url, str) and img_url.startswith('http'):
                            valid_album_urls.append(img_url)

            if not valid_album_urls:
                logging.error(f"API '{api_name}' indicated album, but no valid image URLs found in list for {original_url}. List: {album_list}")
                return {'status': 'failed', 'reason': f"API '{api_name}' 返回无效图集列表", 'original_url': original_url}

            result_data.update({
                'album_aweme_id': aweme_id,
                'album_title': title,
                'album_author_nickname': author_nickname,
                'album_author_id': author_id,
                'album_create_time': create_time,
                'album_list': valid_album_urls,
                # Use first image as cover if specific cover_url wasn't found
                'cover_url': cover_url or (valid_album_urls[0] if valid_album_urls else None),
            })
            logging.info(f"API '{api_name}' successfully fetched album info for {original_url}")
        else:
            # --- Video: Find the NWM URL ---
            nwm_video_url = _get_nested_value(source_dict, NWM_VIDEO_URL_KEYS)

            if not nwm_video_url or not isinstance(nwm_video_url, str) or not nwm_video_url.startswith('http'):
                logging.error(f"Could not find a valid NWM video URL in API '{api_name}' response for {original_url}. Keys tried: {NWM_VIDEO_URL_KEYS}")
                logging.debug(f"Full API source_dict from '{api_name}': {source_dict}")
                return {'status': 'failed', 'reason': f"API '{api_name}' 响应缺少 NWM 视频 URL", 'original_url': original_url}

            result_data.update({
                'video_aweme_id': aweme_id,
                'video_title': title,
                'video_bytes': None, # External APIs provide URL, not bytes
                'nwm_video_url': nwm_video_url, # The found NWM URL
                'video_author_nickname': author_nickname,
                'video_author_id': author_id,
                'video_create_time': create_time,
                'video_music_title': music_title,
                # cover_url already added
            })
            logging.info(f"API '{api_name}' successfully fetched video info for {original_url}")

        logging.debug(f"Final result_data from API '{api_name}': {result_data}")
        return result_data

    except httpx.HTTPStatusError as e_http:
        # Try to get more specific error from response body if possible
        error_detail = e_http.response.text[:200] # Limit length
        try:
            error_json = e_http.response.json()
            error_detail = error_json.get('message', error_detail) # Prefer 'message' key if exists
        except json.JSONDecodeError:
            pass # Keep text snippet if JSON parsing fails
        logging.error(f"API '{api_name}' HTTP Error for {original_url}: Status {e_http.response.status_code} - Detail: {error_detail}")
        # Provide more user-friendly reasons based on status code
        reason = f"API '{api_name}' 请求失败 (HTTP {e_http.response.status_code})"
        if e_http.response.status_code == 401 or e_http.response.status_code == 403:
            reason = f"API '{api_name}' 认证失败 (检查Key/Host)"
        elif e_http.response.status_code == 429:
            reason = f"API '{api_name}' 速率限制"
        elif e_http.response.status_code >= 500:
            reason = f"API '{api_name}' 服务器错误"
        return {'status': 'failed', 'reason': reason, 'original_url': original_url, 'status_code': e_http.response.status_code} # Include status code
    except httpx.TimeoutException as e_timeout:
        logging.error(f"API '{api_name}' Timeout for {original_url}: {e_timeout}")
        return {'status': 'failed', 'reason': f"API '{api_name}' 请求超时", 'original_url': original_url, 'status_code': None}
    except httpx.RequestError as e_req:
        logging.error(f"API '{api_name}' Request Error for {original_url}: {e_req}")
        return {'status': 'failed', 'reason': f"API '{api_name}' 网络或请求错误", 'original_url': original_url, 'status_code': None}
    except Exception as e:
        logging.exception(f"General Error calling API '{api_name}' for {original_url}: {e}")
        return {'status': 'failed', 'reason': f"处理 API '{api_name}' 时发生内部错误", 'original_url': original_url, 'status_code': None}


# --- Main Fetcher Function (Uses Configured External API with Fallback and Retry) ---

async def fetch_tiktok_info(original_url, api_endpoint_configs=None, proxies=None):
    """
    Fetches TikTok video/album information using a list of external API configurations,
    trying them sequentially with retry logic until one succeeds in providing valid NWM data.

    Args:
        original_url (str): The TikTok video/album URL.
        api_endpoint_configs (list, optional): A list of API configuration dictionaries to try. Defaults to None.
        proxies (dict, optional): Dictionary of proxies for the HTTP request. Defaults to None.

    Returns:
        dict: A dictionary containing video/album information or an error dictionary
              if all endpoints fail.
    """
    if not api_endpoint_configs:
        logging.error("No API endpoint configurations provided. Cannot fetch information.")
        return {'status': 'failed', 'reason': '未提供API配置列表', 'original_url': original_url}

    last_error_reason = "所有API尝试均失败" # Default error if loop finishes

    for api_config in api_endpoint_configs:
        api_name = api_config.get('name', 'Unnamed API')
        max_retries = 1 # Number of retries for temporary errors (0 means try once, 1 means try twice total)
        retry_delay = 1.0 # Seconds to wait before retrying

        for attempt in range(max_retries + 1):
            logging.info(f"Attempting API '{api_name}' (Attempt {attempt + 1}/{max_retries + 1}) for URL: {original_url}")
            result = await call_external_tiktok_api(api_config, original_url, proxies=proxies)

            if result.get('status') == 'success':
                # Check if the successful result actually contains the necessary data
                url_type = result.get('url_type')
                if url_type == 'video' and result.get('nwm_video_url'):
                    logging.info(f"Success with API '{api_name}'. Found NWM video URL.")
                    return result # Found valid video data
                elif url_type == 'album' and result.get('album_list'):
                    logging.info(f"Success with API '{api_name}'. Found album list.")
                    return result # Found valid album data
                else:
                    # API reported success but didn't return the expected data
                    logging.warning(f"API '{api_name}' reported success but missing required data (NWM URL or album list). Trying next API.")
                    last_error_reason = f"API '{api_name}' 成功但缺少数据" # Update last error
                    break # Break retry loop for this API, move to the next API config

            else: # API call failed
                status_code = result.get('status_code')
                last_error_reason = result.get('reason', f"API '{api_name}' 请求失败") # Store the reason

                # --- Retry Logic for Temporary Errors ---
                is_temporary_error = (status_code == 429 or (status_code is not None and status_code >= 500)) or "超时" in last_error_reason
                if is_temporary_error and attempt < max_retries:
                    logging.warning(f"API '{api_name}' failed with temporary error (Status: {status_code}, Reason: {last_error_reason}). Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    continue # Continue to the next attempt for this API
                else:
                    # Permanent error or max retries reached for temporary error
                    logging.warning(f"API '{api_name}' failed permanently or after retries. Reason: {last_error_reason}. Trying next API.")
                    break # Break retry loop for this API, move to the next API config
                # --------------------------------------

        # If we broke from the inner loop (failed this API), continue to the next API config in the outer loop
        # If the inner loop completed all retries and still failed, last_error_reason is set, and we continue outer loop

    # If the outer loop completes without returning, all APIs failed
    logging.error(f"All API endpoints failed for URL: {original_url}. Last error: {last_error_reason}")
    return {'status': 'failed', 'reason': last_error_reason, 'original_url': original_url}


# Removed all TikTokApi related code and the old RapidAPI specific function.
# Removed the __main__ block.
