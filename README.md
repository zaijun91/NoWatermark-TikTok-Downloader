# TikTok 批量下载器 (GUI & CLI) / TikTok Batch Downloader (GUI & CLI)

欢迎使用 TikTok 批量下载器！这是一个简单易用的图形界面工具，专门设计用来帮助您轻松批量下载无水印的 TikTok 视频和图集。

**一点说明 (关于 API):** 为了让您第一次使用时更方便，我们尝试在程序启动时自动为您配置几个我们找到的第三方 TikTok 解析 API。这些 API 是用来帮助程序“看懂”您给的 TikTok 链接，并找到无水印视频地址的关键。您可以在程序顶部菜单栏的“设置” -> “API 设置”里看到这些预设的 API。

**请您理解:** 这些预设的 API 通常是公开的免费服务，它们有时可能会因为使用者太多、服务调整或者其他原因变得不稳定或暂时失效。所以，如果您发现下载没反应、失败了，或者下载下来的视频仍然带有水印，**这很可能就是预设 API 的问题，不是程序本身坏了。**

**怎么办呢？** 很简单！遇到这种情况，最好的办法就是去“设置” -> “API 设置”里：
1.  **添加您自己的 API:** 您可以参考下面“配置 API”部分的指引，去网上（比如 RapidAPI Hub）找一个可靠的 API 服务，然后把它添加到列表里。
2.  **激活您的 API:** 添加完成后，选中您添加的那个 API，然后点击“设为活动”按钮。这样程序就会优先使用您自己的、更可靠的 API 来进行下载了。

我们加入预设 API 是为了方便您起步，但长远来看，使用您自己配置的 API 会是更稳定、更可靠的选择。

**最方便的是，项目已包含一个 Windows 安装包 (`Output/TikBoltSetup-v1.1.exe`)！** 您可以直接运行它来安装程序，无需关心 Python 环境或复杂的配置，非常适合普通用户快速上手。

Welcome to the TikTok Batch Downloader! This is a user-friendly graphical tool designed to help you easily batch download TikTok videos and albums without watermarks.

**A Note on APIs:** To make your first experience smoother, we try to automatically configure a few third-party TikTok parsing APIs when you first launch the program. These APIs are crucial as they help the program "understand" the TikTok links you provide and find the watermark-free video sources. You can see these preset APIs under "Settings" -> "API Settings" in the top menu bar.

**Please Understand:** These preset APIs are often public, free services. Sometimes, they might become unstable or temporarily unavailable due to high traffic, service changes, or other reasons. So, if you find that downloads aren't starting, are failing, or the downloaded videos still have watermarks, **it's very likely an issue with the preset API, not a bug in the program itself.**

**What should you do?** It's simple! When this happens, the best approach is to go to "Settings" -> "API Settings" and:
1.  **Add Your Own API:** Follow the guide in the "Configure API" section below to find a reliable API service online (like on RapidAPI Hub) and add it to the list.
2.  **Activate Your API:** After adding it, select your own API from the list and click the "Set Active" button. This tells the program to prioritize using your more dependable API for downloads.

While the presets are there to help you get started, using your own configured API is generally the more stable and reliable option in the long run.

**Most conveniently, the project includes a Windows installer (`Output/TikBoltSetup-v1.1.exe`)!** You can run it directly to install the program without worrying about Python environments or complex configurations, making it perfect for regular users to get started quickly.

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

[**点击此处下载最新安装包 (TikBoltSetup-v1.1.exe)**](https://github.com/zaijun91/NoWatermark-TikTok-Downloader/releases/download/V1.1/TikBoltSetup-v1.1.exe)

**(您可以直接点击上面的链接从 GitHub Releases 下载 v1.1 安装包)**

**(Note: The link above points to the v1.1 release. The current installer is also located in the project's `Output/` directory: `Output/TikBoltSetup-v1.1.exe`)**

### 2. 安装 / Installation

下载 `.exe` 文件后，双击运行安装程序，按照提示完成安装。

After downloading the `.exe` file, double-click to run the installer and follow the prompts to complete the installation.

### 3. 配置 API / Configure API (重要! / Important!)

**首次运行程序时，您可能会在 API 设置中看到一些预设的 API 选项。** 这些是为了方便您快速开始。

**但是，无论是否有预设，您仍然需要检查 API 设置，并确保至少有一个有效的 API 被设为“活动”状态，程序才能正常下载。** 第三方 API 用于获取无水印的视频/图集信息。

**请注意:** 预设的 API 可能来自公共服务，其稳定性或可用性无法保证。如果下载失败或视频仍有水印，强烈建议您自行查找并添加新的、可靠的 API 配置。

**Before running the program for the first time, you might see some pre-configured API options in the API Settings.** These are provided for your convenience to get started quickly.

**However, regardless of presets, you still need to check the API settings and ensure at least one valid API is set as "Active" for the program to download correctly.** These APIs are used to fetch watermark-free video/album information.

**Please note:** Pre-configured APIs might be from public services, and their stability or availability cannot be guaranteed. If downloads fail or videos still have watermarks, it is strongly recommended to find and add new, reliable API configurations yourself.

*   启动程序。
*   启动程序。
*   点击菜单栏的 “设置” -> “API 设置”。
*   **检查列表:** 查看是否已有预设 API。
*   **添加 (如果需要):** 如果列表为空，或预设 API 无效，点击 “添加...” 按钮，输入 API 信息：
    *   **名称:** 给 API 起一个容易识别的名字 (例如 "MyRapidAPI")。
    *   **URL:** API 的请求地址。
    *   **API Key (可选):** 某些 API (如 RapidAPI) 需要 Key。
    *   **API Host (可选):** 某些 API (如 RapidAPI) 需要 Host。
    *   **参数名称 (可选):** API 接收 TikTok 链接的参数名 (默认为 `url`)。
    *   **请求方法 (可选):** 通常是 `GET` (默认) 或 `POST`。
    *   点击 “确定” 保存。
*   **选择并激活:** 从列表中选择一个您认为可靠的 API (无论是预设的还是您自己添加的)，然后**务必点击 “设为活动”**。程序将优先使用标记为“活动”的 API。
*   **提示:** 您可以在网上搜索 "TikTok downloader API" 或访问 [RapidAPI Hub](https://rapidapi.com/hub) 查找可用的 API 服务。添加您自己的 API 通常更稳定可靠。

*   Launch the program.
*   Click on "设置 (Settings)" -> "API 设置 (API Settings)" in the menu bar.
*   **Check the list:** See if there are any pre-configured APIs.
*   **Add (if needed):** If the list is empty, or the preset APIs don't work, click the "添加... (Add...)" button and enter the API information:
    *   **名称 (Name):** Give the API an easily recognizable name (e.g., "MyRapidAPI").
    *   **URL:** The request URL of the API.
    *   **API Key (Optional):** Some APIs (like RapidAPI) require a Key.
    *   **API Host (Optional):** Some APIs (like RapidAPI) require a Host.
    *   **参数名称 (Param Name) (Optional):** The parameter name the API uses for the TikTok link (defaults to `url`).
    *   **请求方法 (Method) (Optional):** Usually `GET` (default) or `POST`.
    *   Click "确定 (OK)" to save.
*   **Select and Activate:** Choose an API you trust from the list (either preset or one you added) and **make sure to click "设为活动 (Set Active)"**. The program will prioritize the API marked as "Active".
*   **Tip:** You can search online for "TikTok downloader API" or visit the [RapidAPI Hub](https://rapidapi.com/hub) to find available API services. Adding your own API is generally more stable and reliable.

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
    git clone https://github.com/zaijun91/NoWatermark-TikTok-Downloader.git
    cd NoWatermark-TikTok-Downloader
    ```

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
