# Python Podcast 播放器

一個使用 Python、Tkinter 和 VLC 開發的桌面 Podcast 播放器。它允許使用者透過 RSS feed 訂閱、管理電台並播放單集。
主要是為了沒有權限安裝軟體的環境做的。

---

## 主要功能

*   **RSS 訂閱**: 從 RSS URL 讀取 Podcast 節目與單集列表。
*   **電台管理**: 管理您的「我的電台」列表（儲存、刪除、匯入、匯出）。
*   **播放清單管理**: 維護一個可匯出/匯入的播放清單與歷史紀錄，支援程式啟動時自動載入上次的播放清單。
*   **進階播放控制**: 完整的播放控制功能，包含播放/暫停、停止、上/下一首、音量調整、可拖曳進度條及變速播放。
*   **智能播放行為**: 點擊單集時自動加入播放清單，切換電台時不清空當前播放清單。
*   **偏好設定**: 可自訂載入單集的數量（全部或僅載入最新 N 集）。
*   **重新整理功能**: 隨時重新載入 RSS feed 獲取最新單集。
*   **狀態保存**: 關閉時自動儲存視窗大小、音量、播放清單及上次收聽的電台與單集。
*   **免安裝**: 直接在 `dist` 資料夾中提供已打包的 `.exe` 執行檔，方便使用。

---

## 系統需求 (所有使用者)

在執行本程式前，請務必完成以下設定：

1.  **作業系統**: Windows
2.  **VLC Media Player**: 本程式使用 VLC 作為音訊播放引擎，這是**必要步驟**。
    *   **下載**: 請至 [VLC 官網](https://www.videolan.org/vlc/) 下載並安裝 VLC Media Player。
    *   **安裝**: 按照安裝程式的指示安裝到預設位置。
    *   **驗證**: 安裝完成後，確認您可以正常啟動 VLC Media Player。

---

## 安裝與執行

您可以根據您的需求，選擇以下兩種方式之一來執行本程式。

### 選項 1: 直接執行 (推薦給一般使用者)

這是最簡單的方式，無需安裝 Python。

1.  **確認系統需求**: 請確保您已完成上述的 **VLC Media Player** 安裝。
2.  **下載執行檔案**:
    *   點擊本儲存庫上方的 `dist/PodcastPlayer` 資料夾。
    *   請將裡面所有裡面下載，放到同一個目錄裡。
3.  **執行**:
    *   下載後，直接雙擊資料夾裡的 `PodcastPlayer.exe` 即可啟動程式。

### 選項 2: 從原始碼執行 (適合開發者)

如果您想查看或修改程式碼，請依照此步驟。

1.  **確認系統需求**:
    *   確保您已完成上述的 **VLC Media Player** 安裝。
    *   確保您的系統已安裝 **Python 3.10** 或更高版本。

2.  **Clone 儲存庫**:
    ```bash
    git clone https://github.com/KennethChenTw/podcast_player.git
    cd podcast_player_v2
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
    **注意**: 需要手動安裝 `python-vlc` 函式庫和確保 VLC Media Player 已正確安裝。

5.  **執行應用程式**:
    ```bash
    python .\src\run.py
    ```

---

## 如何自行打包 (For Developers)

如果您修改了原始碼，並希望自己打包成 `.exe` 檔案：

1.  **安裝 PyInstaller**:
    ```bash
    pip install pyinstaller
    ```

2.  **執行打包命令**:
    (請確保您系統已安裝 VLC Media Player)

    ```cmd
	# 執行建構批次檔 (推薦方式)
    build_exe.bat
    ```
	
    ```cmd
    # 打包成單一資料夾模式 (啟動速度快)
    pyinstaller --name PodcastPlayer --windowed src/podcast_player/main.py
	```

    ```cmd
    # 或者打包成單一檔案模式 (方便分享)
    pyinstaller --name PodcastPlayer --onefile --windowed src/podcast_player/main.py
    ```
    打包後的成品會出現在 `dist` 資料夾中。

---

## 授權 (License)

本專案採用 [MIT License](LICENSE) 進行授權。
