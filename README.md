# TikTok 批量下载器 (GUI & CLI) / TikTok Batch Downloader (GUI & CLI)

这是一个用于批量下载无水印 TikTok 视频和图集的工具，提供了图形用户界面 (GUI) 和命令行界面 (CLI) 两种使用方式。

This is a tool for batch downloading TikTok videos and albums without watermarks. It provides both a Graphical User Interface (GUI) and a Command-Line Interface (CLI).

---

## 主要功能 / Key Features

*   **图形用户界面 (GUI):**
    *   易于使用的界面，适合所有用户。
    *   粘贴或从文件加载多个 TikTok 链接。
    *   管理和配置多个第三方解析 API。
    *   实时显示下载状态、进度和速度。
    *   支持并发下载，提高效率。
    *   可选下载封面和标题。
    *   自定义下载子文件夹结构。
    *   支持网络代理 (系统代理, HTTP/HTTPS, SOCKS5)。
    *   提供浅色和深色主题。
    *   支持多语言 (当前包含中文和英文)。
*   **命令行界面 (CLI):**
    *   通过编辑 `urls.txt` 文件进行批量下载。
    *   适合自动化或服务器环境。
    *   (注意: CLI 版本目前依赖 `tiktok_fetcher.py` 中的 `fetch_tiktok_video_info_rapidapi` 函数，可能需要调整以使用与 GUI 相同的 `fetch_tiktok_info` 逻辑。)

*   **Graphical User Interface (GUI):**
    *   Easy-to-use interface suitable for all users.
    *   Paste or load multiple TikTok links from a file.
    *   Manage and configure multiple third-party parsing APIs.
    *   Real-time display of download status, progress, and speed.
    *   Supports concurrent downloads for improved efficiency.
    *   Optional download of covers and titles.
    *   Customizable download subfolder structure.
    *   Supports network proxies (System Proxy, HTTP/HTTPS, SOCKS5).
    *   Provides light and dark themes.
    *   Supports multiple languages (currently includes Chinese and English).
*   **Command-Line Interface (CLI):**
    *   Batch download by editing the `urls.txt` file.
    *   Suitable for automation or server environments.
    *   (Note: The CLI version currently relies on the `fetch_tiktok_video_info_rapidapi` function in `tiktok_fetcher.py`. It might need adjustments to use the same `fetch_tiktok_info` logic as the GUI.)

---

## 安装与使用 (GUI) / Installation and Usage (GUI)

### 1. 下载安装包 / Download Installer

您可以直接下载预编译的 Windows 安装包 (`.exe`)，无需安装 Python 环境。

You can directly download the pre-compiled Windows installer (`.exe`), no Python environment needed.

**下载链接 / Download Link:**

[**点击此处下载最新安装包 (TikBoltSetup-vX.X.exe)**](PLACEHOLDER_FOR_RELEASE_LINK)

**(注意：上面的链接是占位符，项目上传到 GitHub Releases 后需要替换为实际的下载链接。当前安装包位于项目的 `Output/` 目录下：`Output/TikBoltSetup-v1.1.exe`)**

**(Note: The link above is a placeholder. It needs to be replaced with the actual download link after the project is uploaded to GitHub Releases. The current installer is located in the project's `Output/` directory: `Output/TikBoltSetup-v1.1.exe`)**

### 2. 安装 / Installation

下载 `.exe` 文件后，双击运行安装程序，按照提示完成安装。

After downloading the `.exe` file, double-click to run the installer and follow the prompts to complete the installation.

### 3. 配置 API / Configure API (重要! / Important!)

首次运行程序前或下载失败时，您**必须**配置至少一个有效的第三方 TikTok 解析 API。这些 API 用于获取无水印的视频/图集信息。

Before running the program for the first time or if downloads fail, you **must** configure at least one valid third-party TikTok parsing API. These APIs are used to fetch watermark-free video/album information.

*   启动程序。
*   点击菜单栏的 “设置” -> “API 设置”。
*   点击 “添加...” 按钮。
*   输入 API 的信息：
    *   **名称:** 给 API 起一个容易识别的名字 (例如 "RapidAPI-XYZ")。
    *   **URL:** API 的请求地址。
    *   **API Key (可选):** 某些 API (如 RapidAPI) 需要 Key。
    *   **API Host (可选):** 某些 API (如 RapidAPI) 需要 Host。
    *   **参数名称 (可选):** API 接收 TikTok 链接的参数名 (默认为 `url`)。
    *   **请求方法 (可选):** 通常是 `GET` (默认) 或 `POST`。
*   点击 “确定” 保存。
*   **选择一个 API 并点击 “设为活动”**。程序将优先使用活动 API。
*   **提示:** 您可以在网上搜索 "TikTok downloader API" 或访问 [RapidAPI Hub](https://rapidapi.com/hub) 查找可用的 API 服务。请注意，这些第三方 API 的可用性和稳定性可能会变化。

*   Launch the program.
*   Click on "设置 (Settings)" -> "API 设置 (API Settings)" in the menu bar.
*   Click the "添加... (Add...)" button.
*   Enter the API information:
    *   **名称 (Name):** Give the API an easily recognizable name (e.g., "RapidAPI-XYZ").
    *   **URL:** The request URL of the API.
    *   **API Key (Optional):** Some APIs (like RapidAPI) require a Key.
    *   **API Host (Optional):** Some APIs (like RapidAPI) require a Host.
    *   **参数名称 (Param Name) (Optional):** The parameter name the API uses for the TikTok link (defaults to `url`).
    *   **请求方法 (Method) (Optional):** Usually `GET` (default) or `POST`.
*   Click "确定 (OK)" to save.
*   **Select an API and click "设为活动 (Set Active)"**. The program will prioritize the active API.
*   **Tip:** You can search online for "TikTok downloader API" or visit the [RapidAPI Hub](https://rapidapi.com/hub) to find available API services. Note that the availability and stability of these third-party APIs may vary.

### 4. 配置下载设置 / Configure Download Settings

*   **父级下载路径:** 选择您希望保存下载文件的根目录。
*   **子文件夹模板 (可选):** 自定义每个视频/图集的保存子目录结构。可用变量: `{DATE}`, `{TIME}`, `{AUTHOR_ID}`, `{CUSTOM_TEXT}`。例如: `{DATE}/{AUTHOR_ID}`。
*   **自定义文本 (可选):** 用于子文件夹模板中的 `{CUSTOM_TEXT}` 变量。
*   **并发下载数:** 同时进行的下载任务数量 (建议 3-5)。

*   **父级下载路径 (Parent Download Path):** Choose the root directory where you want to save downloaded files.
*   **子文件夹模板 (Subfolder Template) (Optional):** Customize the subfolder structure for each video/album. Available variables: `{DATE}`, `{TIME}`, `{AUTHOR_ID}`, `{CUSTOM_TEXT}`. Example: `{DATE}/{AUTHOR_ID}`.
*   **自定义文本 (Custom Text) (Optional):** Text used for the `{CUSTOM_TEXT}` variable in the template.
*   **并发下载数 (Concurrent Downloads):** Number of simultaneous download tasks (3-5 recommended).

### 5. 开始下载 / Start Downloading

*   在主界面的大文本框中粘贴 TikTok 链接 (每行一个)，或者点击 “加载文件” 从 `.txt` 文件导入。
*   点击 “开始下载” 按钮。
*   在下方的表格中查看下载进度和状态。

*   Paste TikTok links (one per line) into the large text box on the main screen, or click "加载文件 (Load File)" to import from a `.txt` file.
*   Click the "开始下载 (Start Download)" button.
*   Monitor the download progress and status in the table below.

### 6. 其他设置 / Other Settings

您可以在 “设置” 菜单中调整其他选项：

You can adjust other options in the "设置 (Settings)" menu:

*   **代理设置:** 配置网络代理 (系统, HTTP/HTTPS, SOCKS5)。
*   **封面与标题设置:** 选择是否下载封面图片和标题文本文件，并指定保存路径。
*   **偏好设置 -> 主题设置:** 切换浅色或深色界面主题。
*   **偏好设置 -> 语言设置:** 切换界面语言 (需要重启生效)。

*   **代理设置 (Proxy Settings):** Configure network proxies (System, HTTP/HTTPS, SOCKS5).
*   **封面与标题设置 (Cover & Title Settings):** Choose whether to download cover images and title text files, and specify their save path.
*   **偏好设置 (Preferences) -> 主题设置 (Theme Settings):** Switch between light and dark interface themes.
*   **偏好设置 (Preferences) -> 语言设置 (Language Settings):** Change the interface language (requires restart).

---

## 从源码运行 / Running from Source

如果您想从源代码运行，需要安装 Python 和必要的库。

If you prefer to run from the source code, you need Python and the necessary libraries installed.

1.  **克隆仓库 / Clone Repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
    cd YOUR_REPOSITORY_NAME
    ```
    (请将 `YOUR_USERNAME/YOUR_REPOSITORY_NAME` 替换为实际的仓库地址)
    (Please replace `YOUR_USERNAME/YOUR_REPOSITORY_NAME` with the actual repository path)

2.  **安装依赖 / Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    (建议在虚拟环境中安装 / Recommended to install in a virtual environment)

3.  **运行 GUI / Run GUI:**
    ```bash
    python gui_downloader.py
    ```

4.  **运行 CLI / Run CLI:**
    *   编辑 `urls.txt` 文件，每行放入一个 TikTok 链接。
    *   运行:
        ```bash
        python downloader.py
        ```

---

## 注意事项 / Disclaimer

*   本工具依赖第三方 API 获取信息，API 的可用性和稳定性无法保证。如果下载失败，请尝试更换或添加新的 API 配置。
*   请尊重 TikTok 的服务条款和内容版权。下载的内容仅供个人学习和研究使用，请勿用于商业或其他非法用途。
*   开发者不对使用本工具可能产生的任何后果负责。

*   This tool relies on third-party APIs to fetch information. The availability and stability of these APIs are not guaranteed. If downloads fail, please try changing or adding new API configurations.
*   Please respect TikTok's terms of service and content copyrights. Downloaded content is intended for personal study and research purposes only. Do not use it for commercial or other illegal purposes.
*   The developer is not responsible for any consequences arising from the use of this tool.
