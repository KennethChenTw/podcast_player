# Python Podcast 播放器

一個使用 Python、Tkinter 和 Pygame 開發的桌面 Podcast 播放器。它允許使用者透過 RSS feed 訂閱、管理電台並播放單集。

![App Screenshot](screenshot.png)
*(提示: 執行程式後，擷取一張應用程式的螢幕截圖並命名為 `screenshot.png`，放在專案根目錄下，即可在此處顯示。)*

---

## 主要功能

*   **RSS 訂閱**: 從 RSS URL 讀取 Podcast 節目與單集列表。
*   **電台管理**: 管理您的「我的電台」列表（儲存、刪除、匯入、匯出）。
*   **播放歷史**: 維護一個可匯出/匯入的播放清單與歷史紀錄。
*   **標準播放控制**: 完整的播放控制功能，包含播放/暫停、停止、上/下一首、音量調整及進度條拖曳。
*   **狀態保存**: 關閉時自動儲存視窗大小、音量、上次收聽的電台與單集。
*   **免安裝**: 直接在 `dist` 資料夾中提供已打包的 `.exe` 執行檔，方便使用。

---

## 系統需求 (所有使用者)

在執行本程式前，請務必完成以下設定：

1.  **作業系統**: Windows
2.  **FFmpeg**: 本程式需要 FFmpeg 來進行音訊轉檔，這是**必要步驟**。
    *   **下載**: 請至 [FFmpeg 官網](https://ffmpeg.org/download.html) 下載適合您作業系統的 "release" 版本。
    *   **安裝**: 解壓縮檔案後，您必須將 `ffmpeg.exe` 所在的 `bin` 資料夾路徑**加入到您系統的環境變數 (PATH) 中**。
    *   **驗證**: 安裝完成後，打開一個**新的**命令提示字元視窗並執行 `ffmpeg -version`。如果能成功顯示版本資訊，代表設定正確。

---

## 安裝與執行

您可以根據您的需求，選擇以下兩種方式之一來執行本程式。

### 選項 1: 直接執行 (推薦給一般使用者)

這是最簡單的方式，無需安裝 Python。

1.  **確認系統需求**: 請確保您已完成上述的 **FFmpeg** 設定。
2.  **下載執行檔**:
    *   點擊本儲存庫上方的 `dist` 資料夾。
    *   根據您看到的內容操作：
        *   如果裡面是**一個 `PodcastPlayer.exe` 檔案**，直接點擊它，然後選擇「Download」。
        *   如果裡面是**一個 `PodcastPlayer` 資料夾**，請將整個資料夾下載下來。
3.  **執行**:
    *   下載後，直接雙擊 `PodcastPlayer.exe` 即可啟動程式。

### 選項 2: 從原始碼執行 (適合開發者)

如果您想查看或修改程式碼，請依照此步驟。

1.  **確認系統需求**:
    *   確保您已完成上述的 **FFmpeg** 設定。
    *   確保您的系統已安裝 **Python 3.9** 或更高版本。

2.  **Clone 儲存庫**:
    ```bash
    git clone https://github.com/KennethChenTw/podcast_player.git
    cd podcast_player
    ```

3.  **(建議) 建立並啟用虛擬環境**:
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

4.  **安裝 Python 依賴套件**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **執行應用程式**:
    ```bash
    python podcast_player.py
    ```

---

## 如何自行打包 (For Developers)

如果您修改了原始碼，並希望自己打包成 `.exe` 檔案：

1.  **安裝 PyInstaller**:
    ```bash
    pip install pyinstaller
    ```

2.  **執行打包命令**:
    (請確保您系統的 PATH 中已經可以找到 `ffmpeg.exe`)
    ```bash
    # 打包成單一資料夾模式 (啟動速度快)
    pyinstaller --name PodcastPlayer --windowed podcast_player.py

    # 或者打包成單一檔案模式 (方便分享)
    pyinstaller --name PodcastPlayer --onefile --windowed podcast_player.py
    ```
    打包後的成品會出現在 `dist` 資料夾中。

---

## 授權 (License)

本專案採用 [MIT License](LICENSE) 進行授權。
